"""문제 은행 로더.

`data/questions/*.json` 을 디렉토리 스캔 방식으로 읽어 메모리에 캐싱한다.
카테고리 목록은 어디에도 하드코딩하지 않으며, 파일이 추가되면 앱 재시작만으로 반영된다.

스키마(문항 1건):
  공통      : id, category, type, difficulty, question, explanation
  mcq       : choices[list[str]], answer_index[int]
  subjective: model_answer[str], keywords[list[str]]

스키마를 위반한 문항은 **해당 문항만** 건너뛰고 경고 로그를 남긴다 (파일 전체를 버리지 않는다).
"""

from __future__ import annotations

import json
import logging
import os
import random
import re
import unicodedata
from pathlib import Path
from typing import Any, Iterable

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

QUESTION_TYPES = ("mcq", "subjective")
DIFFICULTIES = ("basic", "intermediate", "advanced")
DEFAULT_DIFFICULTY = "intermediate"

#: 클라이언트로 절대 내보내지 않는 필드. answer_index/model_answer 뿐 아니라
#: keywords(주관식 정답 힌트)와 explanation(정답이 그대로 서술됨)도 함께 제거한다.
SECRET_FIELDS = ("answer_index", "model_answer", "keywords", "explanation")

#: 콘텐츠 스킬 규격상 MCQ 선택지는 정확히 이 개수여야 한다.
#: 개수가 다르면 문항을 버리지 않고 경고 로그만 남긴다 — 콘텐츠 편집 중 일시적으로
#: 개수가 어긋날 수 있고, 문항을 버리면 그 사실이 오히려 드러나지 않기 때문이다.
MCQ_EXPECTED_CHOICES = 4

#: 선택지 라벨(A~H) 렌더링이 안전한 상한. 이를 넘으면 템플릿이 숫자 라벨로 폴백한다.
MCQ_LABELED_CHOICES = 8

#: 주관식 정답 처리 임계값 — 키워드 포함 비율이 이 값 이상이면 정답 처리
SUBJECTIVE_PASS_RATIO = 0.6

#: 키워드 하나를 "포함"으로 인정하는 토큰 매칭 비율.
#: 키워드가 여러 하위 개념을 나열한 서술형('node-local / rack-local / off-switch')인 경우가
#: 많아, 구문 전체 부분문자열 매칭은 영구 미매칭이 된다. 토큰 절반 이상이 답안에 나타나면
#: 해당 키워드를 다룬 것으로 본다.
KEYWORD_TOKEN_RATIO = 0.5

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_QUESTIONS_DIR = _PROJECT_ROOT / "data" / "questions"

#: 카테고리 파일명 → 화면 표시용 라벨. 목록 자체는 스캔 결과에서 나오고,
#: 여기에 없는 카테고리는 파일명을 그대로 예쁘게 다듬어 표시한다.
_LABEL_OVERRIDES = {
    "hdfs": "HDFS",
    "sql": "SQL",
    "k8s": "Kubernetes",
    "yarn": "YARN",
    "rest-api": "REST API",
    "clickhouse": "ClickHouse",
    "elasticsearch": "Elasticsearch",
    "kafka": "Kafka",
    "kafka-streams": "Kafka Streams",
    "spark": "Spark",
    "spark-streaming": "Spark Streaming",
    "hadoop": "Hadoop",
    "hive": "Hive",
    "trino": "Trino",
    "iceberg": "Iceberg",
    "kibana": "Kibana",
    "scala": "Scala",
    "python": "Python",
    "java": "Java",
    "git": "Git",
    "ranger": "Ranger",
}


def questions_dir() -> Path:
    """문제 은행 디렉토리. 환경변수 QUESTIONS_DIR 로 재정의할 수 있다."""
    override = os.environ.get("QUESTIONS_DIR")
    return Path(override).resolve() if override else _DEFAULT_QUESTIONS_DIR


def label_for(category: str) -> str:
    if category in _LABEL_OVERRIDES:
        return _LABEL_OVERRIDES[category]
    return category.replace("-", " ").replace("_", " ").title()


# ---------------------------------------------------------------------------
# 텍스트 정규화 / 주관식 채점
# ---------------------------------------------------------------------------

_NON_WORD = re.compile(r"[^0-9a-z가-힣ㄱ-ㆎ]+")


def normalize(text: str) -> str:
    """비교용 정규화: NFKC → 소문자 → 공백/문장부호 제거.

    한국어 키워드('컨슈머 그룹')와 사용자 입력('컨슈머그룹')을 같게 보기 위해
    공백까지 제거한 뒤 부분 문자열로 비교한다.
    """
    text = unicodedata.normalize("NFKC", text or "").lower()
    return _NON_WORD.sub("", text)


#: 키워드 안에서 "여러 대안 중 하나"를 나열하는 구분자.
#: 'node-local / rack-local / off-switch' → 세 대안 중 하나만 나와도 그 개념을 안다고 본다.
_ALT_SPLIT = re.compile(r"\s*(?:[/|·,;]|\bvs\.?\b|\bor\b|또는)\s*", re.IGNORECASE)

#: 하나의 대안 안에서 단어를 쪼개는 구분자.
#: '-' 는 쪼개지 않는다 — normalize() 가 어차피 제거하므로 'node-local' 은 한 토큰으로 둔다.
_WORD_SPLIT = re.compile(r"[\s+→~^&()\[\]{}:<>=]+")

#: 매칭 신호가 없는 조사·접속어. 정규화 후 형태로 적는다.
_TOKEN_STOPWORDS = frozenset({
    "및", "또는", "그리고", "또한", "등", "여부", "관련", "사용", "경우", "때",
    "vs", "and", "or", "of", "the", "a", "an", "to", "in", "for", "with",
})

#: 이 길이 미만의 토큰은 우연 매칭이 잦아 버린다.
_MIN_TOKEN_LEN = 2


def _tokenize_keyword(keyword: str) -> list[list[str]]:
    """키워드를 [대안[토큰]] 구조로 분해한다.

    'node-local / rack-local / off-switch' → [['nodelocal'], ['racklocal'], ['offswitch']]
    'ReplicatedMergeTree + Keeper'         → [['replicatedmergetree', 'keeper']]
    """
    groups: list[list[str]] = []
    for alternative in _ALT_SPLIT.split(keyword or ""):
        tokens = []
        for word in _WORD_SPLIT.split(alternative):
            token = normalize(word)
            if len(token) >= _MIN_TOKEN_LEN and token not in _TOKEN_STOPWORDS:
                tokens.append(token)
        if tokens:
            groups.append(tokens)
    return groups


def keyword_matches(keyword: str, normalized_answer: str) -> bool:
    """키워드가 답안에서 다뤄졌는지 토큰 단위로 판정한다.

    1) 키워드 구문 전체가 그대로 등장하면 매칭 (가장 강한 신호)
    2) 나열된 대안 중 어느 하나가 통째로 등장하면 매칭
    3) 그 외에는 전체 토큰 중 절반 이상 **그리고 최소 2개**가 등장하면 매칭
       (토큰이 2개뿐인 키워드에서 1개만 맞아도 통과되는 반쪽 매칭을 차단한다 —
       예: "런타임 통계" 중 "통계"만 언급해도 정답 처리되던 문제)
    """
    if not normalized_answer:
        return False

    whole = normalize(keyword)
    if whole and whole in normalized_answer:
        return True

    groups = _tokenize_keyword(keyword)
    if not groups:
        return False

    # 어느 한 대안의 토큰이 전부 등장하면 그 개념을 서술한 것으로 본다.
    for tokens in groups:
        if all(token in normalized_answer for token in tokens):
            return True

    flat = [token for tokens in groups for token in tokens]
    hits = sum(1 for token in flat if token in normalized_answer)
    if not hits:
        return False
    if len(flat) >= 2 and hits < 2:
        return False
    return hits / len(flat) >= KEYWORD_TOKEN_RATIO


def grade_subjective(answer: str, keywords: list[str]) -> dict[str, Any]:
    """키워드 포함 비율로 부분 점수를 계산한다 (키워드별 판정은 토큰 단위)."""
    normalized_answer = normalize(answer)
    matched: list[str] = []
    missed: list[str] = []

    for keyword in keywords:
        if keyword_matches(keyword, normalized_answer):
            matched.append(keyword)
        else:
            missed.append(keyword)

    if not keywords:
        # 키워드가 없는 문항은 자동 채점 불가 → 작성 여부만 확인하고 리뷰로 넘긴다.
        score = 1.0 if normalized_answer else 0.0
    else:
        score = len(matched) / len(keywords)

    return {
        "score": round(score, 4),
        "correct": score >= SUBJECTIVE_PASS_RATIO,
        "matched_keywords": matched,
        "missed_keywords": missed,
        "keyword_total": len(keywords),
    }


# ---------------------------------------------------------------------------
# 검증
# ---------------------------------------------------------------------------

class SkippedQuestion(ValueError):
    """스키마 위반으로 건너뛴 문항."""


def _require_text(record: dict, field: str) -> str:
    value = record.get(field)
    if not isinstance(value, str) or not value.strip():
        raise SkippedQuestion(f"'{field}' 필드가 비어 있거나 문자열이 아님")
    return value.strip()


def _validate(record: Any, fallback_category: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise SkippedQuestion(f"문항이 객체가 아님 ({type(record).__name__})")

    qid = _require_text(record, "id")
    question = _require_text(record, "question")

    qtype = record.get("type")
    if qtype not in QUESTION_TYPES:
        raise SkippedQuestion(f"type 값이 유효하지 않음: {qtype!r}")

    category = record.get("category")
    if not isinstance(category, str) or not category.strip():
        category = fallback_category
    category = category.strip()

    difficulty = record.get("difficulty")
    if difficulty not in DIFFICULTIES:
        logger.warning("[%s] difficulty=%r → '%s' 로 보정", qid, difficulty, DEFAULT_DIFFICULTY)
        difficulty = DEFAULT_DIFFICULTY

    clean: dict[str, Any] = {
        "id": qid,
        "category": category,
        "type": qtype,
        "difficulty": difficulty,
        "question": question,
        "explanation": (record.get("explanation") or "").strip(),
    }

    if qtype == "mcq":
        choices = record.get("choices")
        if not isinstance(choices, list) or len(choices) < 2:
            raise SkippedQuestion("mcq 문항의 choices 가 2개 미만이거나 리스트가 아님")
        if not all(isinstance(c, str) and c.strip() for c in choices):
            raise SkippedQuestion("mcq 문항의 choices 에 빈 값이 있음")
        if len(choices) != MCQ_EXPECTED_CHOICES:
            # 규격 위반이지만 문항은 살린다. 어떤 문항인지 id 로 특정할 수 있게 남긴다.
            logger.warning(
                "[%s] 규격 위반: mcq choices 가 %d개입니다 (규격 %d개). 문항은 유지하되 콘텐츠 수정이 필요합니다",
                qid, len(choices), MCQ_EXPECTED_CHOICES,
            )
        if len(choices) > MCQ_LABELED_CHOICES:
            logger.warning(
                "[%s] mcq choices 가 %d개로 라벨 상한(%d)을 넘어 %d번째부터 숫자 라벨로 표시됩니다",
                qid, len(choices), MCQ_LABELED_CHOICES, MCQ_LABELED_CHOICES + 1,
            )
        answer_index = record.get("answer_index")
        if isinstance(answer_index, bool) or not isinstance(answer_index, int):
            raise SkippedQuestion(f"answer_index 가 정수가 아님: {answer_index!r}")
        if not 0 <= answer_index < len(choices):
            raise SkippedQuestion(
                f"answer_index({answer_index}) 가 choices 범위(0~{len(choices) - 1})를 벗어남"
            )
        clean["choices"] = [c.strip() for c in choices]
        clean["answer_index"] = answer_index
    else:
        clean["model_answer"] = _require_text(record, "model_answer")
        keywords = record.get("keywords")
        if keywords is None:
            keywords = []
        if not isinstance(keywords, list):
            raise SkippedQuestion("keywords 가 리스트가 아님")
        clean["keywords"] = [k.strip() for k in keywords if isinstance(k, str) and k.strip()]
        if not clean["keywords"]:
            logger.warning("[%s] keywords 가 비어 있어 부분 점수 계산이 불가합니다", qid)

    return clean


# ---------------------------------------------------------------------------
# 문제 은행
# ---------------------------------------------------------------------------

class QuestionBank:
    """디렉토리 스캔으로 로드한 문제 은행 (앱 시작 시 1회 로드 후 메모리 캐싱)."""

    def __init__(self, directory: Path | str | None = None) -> None:
        self.directory = Path(directory) if directory else questions_dir()
        self._by_category: dict[str, list[dict]] = {}
        self._by_id: dict[str, dict] = {}
        self.load_errors: list[str] = []
        self.skipped_count = 0

    # -- 로딩 ---------------------------------------------------------------

    def load(self) -> "QuestionBank":
        self._by_category.clear()
        self._by_id.clear()
        self.load_errors.clear()
        self.skipped_count = 0

        if not self.directory.is_dir():
            msg = f"문제 은행 디렉토리를 찾을 수 없습니다: {self.directory}"
            logger.warning(msg)
            self.load_errors.append(msg)
            return self

        for path in sorted(self.directory.glob("*.json")):
            self._load_file(path)

        logger.info(
            "문제 은행 로드 완료: %d개 카테고리 / %d문항 (건너뜀 %d)",
            len(self._by_category), len(self._by_id), self.skipped_count,
        )
        return self

    def _load_file(self, path: Path) -> None:
        category = path.stem
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            msg = f"{path.name}: 파일을 읽을 수 없어 건너뜁니다 ({exc})"
            logger.warning(msg)
            self.load_errors.append(msg)
            return

        # 최상위가 배열이거나 {"questions": [...]} 형태 둘 다 허용
        if isinstance(raw, dict):
            raw = raw.get("questions", [])
        if not isinstance(raw, list):
            msg = f"{path.name}: 최상위가 배열이 아니어서 건너뜁니다"
            logger.warning(msg)
            self.load_errors.append(msg)
            return

        accepted: list[dict] = []
        for position, record in enumerate(raw):
            try:
                question = _validate(record, fallback_category=category)
            except SkippedQuestion as exc:
                self.skipped_count += 1
                msg = f"{path.name}[{position}]: {exc}"
                logger.warning("문항 건너뜀 — %s", msg)
                self.load_errors.append(msg)
                continue

            if question["id"] in self._by_id:
                self.skipped_count += 1
                msg = f"{path.name}[{position}]: id 중복 '{question['id']}' — 건너뜁니다"
                logger.warning(msg)
                self.load_errors.append(msg)
                continue

            self._by_id[question["id"]] = question
            accepted.append(question)

        if not accepted:
            msg = f"{path.name}: 유효한 문항이 없어 카테고리 목록에서 제외합니다"
            logger.warning(msg)
            self.load_errors.append(msg)
            return

        self._by_category[category] = accepted

    # -- 조회 ---------------------------------------------------------------

    @property
    def is_empty(self) -> bool:
        return not self._by_category

    @property
    def total_questions(self) -> int:
        return len(self._by_id)

    def has_category(self, category: str) -> bool:
        return category in self._by_category

    def get(self, question_id: str) -> dict | None:
        return self._by_id.get(question_id)

    def all_questions(self) -> list[dict]:
        return list(self._by_id.values())

    def categories(self) -> list[dict[str, Any]]:
        """카테고리별 통계. 정렬 기준은 표시 라벨."""
        result = []
        for category, questions in self._by_category.items():
            counts_by_difficulty = {d: 0 for d in DIFFICULTIES}
            mcq = subjective = 0
            for q in questions:
                counts_by_difficulty[q["difficulty"]] += 1
                if q["type"] == "mcq":
                    mcq += 1
                else:
                    subjective += 1
            result.append({
                "id": category,
                "label": label_for(category),
                "total": len(questions),
                "mcq": mcq,
                "subjective": subjective,
                "difficulty": counts_by_difficulty,
            })
        result.sort(key=lambda c: c["label"].lower())
        return result

    def sample(
        self,
        category: str | None = None,
        qtype: str | None = None,
        difficulty: str | None = None,
        count: int = 10,
    ) -> list[dict]:
        """조건에 맞는 문항을 랜덤 추출한다. 요청 수보다 적으면 있는 만큼 반환."""
        if category and category != "all":
            pool: Iterable[dict] = self._by_category.get(category, [])
        else:
            pool = self.all_questions()

        filtered = [
            q for q in pool
            if (not qtype or qtype == "all" or q["type"] == qtype)
            and (not difficulty or difficulty == "all" or q["difficulty"] == difficulty)
        ]
        if count >= len(filtered):
            selected = list(filtered)
            random.shuffle(selected)
            return selected
        return random.sample(filtered, count)

    # -- 직렬화 -------------------------------------------------------------

    @staticmethod
    def to_public(question: dict) -> dict:
        """정답 관련 필드를 제거한 클라이언트 전송용 사본."""
        return {k: v for k, v in question.items() if k not in SECRET_FIELDS}

    # -- 채점 ---------------------------------------------------------------

    def grade(self, question_id: str, answer: Any) -> dict[str, Any]:
        """서버 사이드 단일 문항 채점. 정답 정보는 채점 후에만 응답에 포함된다."""
        question = self.get(question_id)
        if question is None:
            return {
                "question_id": question_id,
                "error": "존재하지 않는 문항입니다",
                "correct": False,
                "score": 0.0,
            }

        base = {
            "question_id": question_id,
            "category": question["category"],
            "type": question["type"],
            "difficulty": question["difficulty"],
            "question": question["question"],
            "explanation": question["explanation"],
        }

        if question["type"] == "mcq":
            try:
                selected = int(answer)
            except (TypeError, ValueError):
                selected = -1
            correct = selected == question["answer_index"]
            base.update({
                "choices": question["choices"],
                "answer_index": question["answer_index"],
                "selected_index": selected if selected >= 0 else None,
                "answered": selected >= 0,
                "correct": correct,
                "score": 1.0 if correct else 0.0,
            })
            return base

        text = answer if isinstance(answer, str) else ""
        result = grade_subjective(text, question["keywords"])
        base.update({
            "user_answer": text.strip(),
            "model_answer": question["model_answer"],
            "keywords": question["keywords"],
            "answered": bool(text.strip()),
            "pass_ratio": SUBJECTIVE_PASS_RATIO,
            **result,
        })
        return base
