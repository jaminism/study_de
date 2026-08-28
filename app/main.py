"""데이터 엔지니어 학습 문제 풀이 웹앱 (Flask).

실행:  python app/main.py   →  http://127.0.0.1:5000

라우트
  GET  /                                     카테고리 선택
  GET  /quiz                                 문제 풀이 화면
  GET  /result/<result_id>                   결과 리뷰
  GET  /api/categories                       카테고리별 문항 수
  GET  /api/questions/<category>             랜덤 N문항 (정답 필드 제외)
  POST /api/submit                           서버 사이드 채점
"""

from __future__ import annotations

import logging
import os
import secrets
import uuid
from collections import OrderedDict
from typing import Any

from flask import (
    Flask,
    jsonify,
    render_template,
    request,
    session,
    url_for,
)

from data_loader import (
    DIFFICULTIES,
    QUESTION_TYPES,
    QuestionBank,
    label_for,
)

logging.basicConfig(
    level=os.environ.get("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
)
logger = logging.getLogger("quiz")

MAX_COUNT = 50
DEFAULT_COUNT = 10
#: 결과는 쿠키 용량 한계를 넘으므로 서버 메모리에 보관한다 (학습용 단일 프로세스 전제).
RESULT_CACHE_LIMIT = 200

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
app.json.ensure_ascii = False

bank = QuestionBank().load()

_results: "OrderedDict[str, dict]" = OrderedDict()


def _store_result(payload: dict) -> str:
    result_id = uuid.uuid4().hex
    _results[result_id] = payload
    while len(_results) > RESULT_CACHE_LIMIT:
        _results.popitem(last=False)
    return result_id


def _clamp_count(raw: str | None) -> int:
    try:
        count = int(raw) if raw is not None else DEFAULT_COUNT
    except (TypeError, ValueError):
        count = DEFAULT_COUNT
    return max(1, min(count, MAX_COUNT))


def _normalize_choice(raw: str | None, allowed: tuple[str, ...]) -> str:
    value = (raw or "all").strip().lower()
    return value if value in allowed or value == "all" else "all"


# ---------------------------------------------------------------------------
# 화면
# ---------------------------------------------------------------------------

@app.route("/")
def index():
    categories = bank.categories()
    return render_template(
        "index.html",
        categories=categories,
        total_questions=bank.total_questions,
        difficulties=DIFFICULTIES,
        questions_dir=str(bank.directory),
        load_errors=bank.load_errors,
        is_empty=bank.is_empty,
    )


@app.route("/quiz")
def quiz():
    category = (request.args.get("category") or "all").strip()
    if category != "all" and not bank.has_category(category):
        return render_template(
            "index.html",
            categories=bank.categories(),
            total_questions=bank.total_questions,
            difficulties=DIFFICULTIES,
            questions_dir=str(bank.directory),
            load_errors=bank.load_errors,
            is_empty=bank.is_empty,
            error=f"'{category}' 카테고리를 찾을 수 없습니다.",
        ), 404

    return render_template(
        "quiz.html",
        category=category,
        category_label="전체 카테고리" if category == "all" else label_for(category),
        qtype=_normalize_choice(request.args.get("type"), QUESTION_TYPES),
        difficulty=_normalize_choice(request.args.get("difficulty"), DIFFICULTIES),
        count=_clamp_count(request.args.get("count")),
    )


@app.route("/result/<result_id>")
def result(result_id: str):
    payload = _results.get(result_id)
    if payload is None:
        return render_template("result.html", payload=None, result_id=result_id), 404
    return render_template("result.html", payload=payload, result_id=result_id)


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------

@app.get("/api/categories")
def api_categories():
    return jsonify({
        "categories": bank.categories(),
        "total_categories": len(bank.categories()),
        "total_questions": bank.total_questions,
        "source_dir": str(bank.directory),
        "skipped": bank.skipped_count,
    })


@app.get("/api/questions/<category>")
def api_questions(category: str):
    if category != "all" and not bank.has_category(category):
        return jsonify({"error": f"unknown category: {category}"}), 404

    qtype = _normalize_choice(request.args.get("type"), QUESTION_TYPES)
    difficulty = _normalize_choice(request.args.get("difficulty"), DIFFICULTIES)
    count = _clamp_count(request.args.get("count"))

    picked = bank.sample(category=category, qtype=qtype, difficulty=difficulty, count=count)
    public = [QuestionBank.to_public(q) for q in picked]

    # 현재 세트의 문제 ID와 진행률을 세션에 보관한다.
    # /api/submit 은 이 목록에 있는 문항만 채점해 임의 문항 조회를 막는다.
    session["set"] = {
        "ids": [q["id"] for q in public],
        "category": category,
        "type": qtype,
        "difficulty": difficulty,
        "answered": 0,
    }
    session.modified = True

    return jsonify({
        "category": category,
        "type": qtype,
        "difficulty": difficulty,
        "requested": count,
        "returned": len(public),
        "questions": public,
    })


@app.post("/api/submit")
def api_submit():
    """서버 사이드 채점.

    단건:  {"question_id": "kafka-mcq-001", "answer": 1}
    일괄:  {"answers": [{"question_id": "...", "answer": ...}, ...]}
    """
    body: Any = request.get_json(silent=True) or {}
    if not isinstance(body, dict):
        return jsonify({"error": "JSON 객체가 필요합니다"}), 400

    if "answers" in body:
        submissions = body.get("answers")
        batch = True
    else:
        submissions = [body]
        batch = False

    if not isinstance(submissions, list) or not submissions:
        return jsonify({"error": "채점할 답안이 없습니다"}), 400

    # fail-closed: 진행 중인 문제 세트가 없으면 채점 자체를 거부한다.
    # (세션이 없을 때 검사를 건너뛰면 문항 ID만 알아도 정답/해설을 수집할 수 있다.)
    allowed = set((session.get("set") or {}).get("ids") or [])
    if not allowed:
        return jsonify({
            "error": "진행 중인 문제 세트가 없습니다. 문제를 먼저 불러오세요."
        }), 403

    graded: list[dict] = []
    for item in submissions:
        if not isinstance(item, dict):
            return jsonify({"error": "각 답안은 객체여야 합니다"}), 400
        question_id = item.get("question_id")
        if not isinstance(question_id, str) or not question_id:
            return jsonify({"error": "question_id 가 필요합니다"}), 400
        if question_id not in allowed:
            return jsonify({
                "error": f"현재 세션의 문제 세트에 없는 문항입니다: {question_id}"
            }), 403
        graded.append(bank.grade(question_id, item.get("answer")))

    answered = sum(1 for g in graded if g.get("answered"))
    if session.get("set"):
        session["set"]["answered"] = answered
        session.modified = True

    if not batch:
        return jsonify(graded[0])

    total = len(graded)
    score_sum = sum(float(g.get("score") or 0.0) for g in graded)
    correct = sum(1 for g in graded if g.get("correct"))
    current = session.get("set") or {}

    payload = {
        "summary": {
            "total": total,
            "answered": answered,
            "correct": correct,
            "score": round(score_sum, 4),
            "percentage": round(score_sum / total * 100, 1) if total else 0.0,
            "mcq_total": sum(1 for g in graded if g.get("type") == "mcq"),
            "mcq_correct": sum(1 for g in graded if g.get("type") == "mcq" and g.get("correct")),
            "subjective_total": sum(1 for g in graded if g.get("type") == "subjective"),
            "subjective_correct": sum(
                1 for g in graded if g.get("type") == "subjective" and g.get("correct")
            ),
            "category": current.get("category", "all"),
            "category_label": (
                "전체 카테고리" if current.get("category", "all") == "all"
                else label_for(current.get("category", "all"))
            ),
            "difficulty": current.get("difficulty", "all"),
            "type": current.get("type", "all"),
        },
        "results": graded,
    }
    result_id = _store_result(payload)
    payload["result_id"] = result_id
    payload["result_url"] = url_for("result", result_id=result_id)
    session["last_result_id"] = result_id
    return jsonify(payload)


@app.get("/api/health")
def api_health():
    return jsonify({
        "status": "ok" if not bank.is_empty else "empty",
        "categories": len(bank.categories()),
        "questions": bank.total_questions,
        "skipped": bank.skipped_count,
    })


if __name__ == "__main__":
    if bank.is_empty:
        logger.warning("문제 은행이 비어 있습니다 (%s)", bank.directory)
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        debug=os.environ.get("FLASK_DEBUG", "0") == "1",
    )
