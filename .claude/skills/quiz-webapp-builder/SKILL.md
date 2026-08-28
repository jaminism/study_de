---
name: quiz-webapp-builder
description: "생성된 면접 문제 은행(data/questions/*.json)을 기반으로 Python 웹 애플리케이션(Flask)을 빌드한다. 객관식/주관식 문제 풀이, 채점, 카테고리 선택, 결과 리뷰 기능을 구현할 때 사용. '앱 만들어줘', '웹 서비스 빌드', '문제 풀이 화면 구현' 요청 시 반드시 이 스킬을 사용할 것."
---

# 면접 문제 풀이 웹앱 빌드 스킬

`data/questions/{category}.json` 문제 은행을 서빙하는 Python 웹 애플리케이션을 구축하는 절차.

## 왜 Flask인가
요구사항은 "파이썬, 웹환경"만 명시하고 프레임워크를 지정하지 않았다. Flask는 의존성이 가볍고 Jinja2 템플릿으로 서버 렌더링이 가능해, 별도 프론트엔드 빌드 체인 없이 빠르게 학습용 앱을 완성할 수 있다. 이미 FastAPI/Django 등 프로젝트 관례가 생겼다면 그것을 우선한다.

## 아키텍처

```
app/
├── main.py              # Flask 앱, 라우트
├── data_loader.py        # data/questions/*.json 로드 및 캐싱
├── templates/
│   ├── index.html        # 카테고리 선택
│   ├── quiz.html          # 문제 풀이 화면
│   └── result.html        # 결과 리뷰
├── static/
│   └── style.css
└── requirements.txt
```

## 데이터 로딩 원칙
- 앱 시작 시 `data/questions/*.json`을 전부 로드해 메모리에 캐싱한다 (파일 I/O를 매 요청마다 반복하지 않는다)
- 카테고리 파일이 없거나 비어 있으면 해당 카테고리를 목록에서 제외하고 경고 로그만 남긴다 (앱이 죽지 않게)
- `interview-question-research` 스킬의 스키마를 그대로 신뢰하되, 필드 누락 시 해당 문항만 건너뛰고 나머지는 로드한다

## API 설계

| 메서드 | 경로 | 설명 |
|--------|------|------|
| GET | `/api/categories` | 카테고리별 문항 수 목록 (`data/questions/` 디렉토리 스캔 결과) |
| GET | `/api/questions/<category>?type=mcq\|subjective&count=N` | 랜덤 N개 문제 (정답 필드 제외하고 반환) |
| POST | `/api/submit` | `{question_id, answer}` → 채점 결과 |

**정답 필드를 프론트로 보내지 않는다** — `/api/questions`는 `answer_index`, `model_answer`를 제거한 뒤 응답한다. 채점은 서버(`/api/submit`)에서만 수행해, 브라우저 개발자 도구로 정답을 미리 볼 수 없게 한다.

## 채점 로직
- MCQ: `answer_index`와 사용자 선택 인덱스를 비교 → boolean
- 주관식: 정확 매칭이 아닌 `keywords` 포함 비율로 부분 점수 계산 (예: 5개 중 3개 키워드 포함 → 60%). 모범 답안(`model_answer`)은 채점 후 함께 반환해 사용자가 비교할 수 있게 한다

## 세션/상태 관리
Flask `session`으로 현재 세트의 문제 ID 목록과 진행률을 저장한다. 별도 DB 없이 학습용 세션 상태만 필요하므로 서버 메모리/쿠키 기반으로 충분하다.

## 재실행 시 동작
`data/questions/`에 새 카테고리 파일이 추가되면 앱 재시작만으로 자동 반영되어야 한다 (하드코딩된 카테고리 목록 금지, 디렉토리 스캔 방식 사용).

## 테스트 방법
로컬에서 `python app/main.py` 실행 후, `/api/categories`가 `data/questions/`의 파일 목록과 일치하는지, `/api/questions/kafka?type=mcq&count=5`가 정답 필드 없이 5문항을 반환하는지 확인한다.
