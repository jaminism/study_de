---
name: content-app-qa
description: "학습 문제 은행(data/questions/*.json)과 웹앱(app/)의 통합 정합성을 검증한다. 스키마 위반, ID 중복, answer_index 범위 오류, API↔프론트 경계면 불일치를 교차 비교로 찾아낸다. '문제 은행 검증', 'QA 해줘', '앱 점검' 요청 시 반드시 이 스킬을 사용할 것."
---

# 콘텐츠·앱 통합 QA 스킬

문제 은행과 웹앱이 각각은 정상이어도 연결 지점에서 어긋나는 결함을 찾는다. 존재 확인이 아니라 **양쪽을 동시에 읽는 교차 비교**가 핵심이다.

## 검증 우선순위
1. **콘텐츠 스키마 정합성** — 각 파일 내부의 구조적 결함
2. **콘텐츠 ↔ 앱 경계면 정합성** — data_loader.py가 실제로 스키마를 올바르게 소비하는지
3. **API ↔ 프론트 경계면 정합성** — API 응답 shape과 프론트 JS가 기대하는 shape 일치 여부

## 1. 콘텐츠 스키마 검증

`data/questions/*.json`을 각각 Read하고 확인한다:
- [ ] `id`가 파일 내에서 유일한가 (중복 ID 검색)
- [ ] MCQ의 `choices`가 정확히 4개이고 `answer_index`가 0~3 범위인가
- [ ] 모든 문항에 `explanation`이 비어있지 않은가
- [ ] 주관식의 `keywords`가 3~5개인가
- [ ] `category` 필드가 파일명과 일치하는가
- [ ] 난이도 분포가 basic/intermediate/advanced 모두 존재하는가 (한 난이도로 편중 시 경고)

## 2. 콘텐츠 ↔ 앱 경계면 검증

**양쪽을 동시에 열어 비교한다:**

| 왼쪽 (생산자) | 오른쪽 (소비자) | 확인할 것 |
|--------------|---------------|-----------|
| `data/questions/{category}.json`의 필드명 | `app/data_loader.py`의 필드 접근 코드 | 필드명 오타·case 불일치로 조용히 None을 반환하는 곳이 없는가 |
| 카테고리 파일 목록 (디렉토리 스캔) | `app/main.py`의 `/api/categories` 응답 | 하드코딩된 카테고리 리스트가 있으면 지적 (신규 파일 추가 시 반영 안 됨) |
| MCQ `answer_index`/주관식 `model_answer` | `/api/questions` 응답 payload | 정답 필드가 실제로 응답에서 제거되는지 (제거 안 되면 정답 유출 버그) |

## 3. API ↔ 프론트 경계면 검증

- [ ] `/api/questions`가 반환하는 JSON의 키와 `templates/quiz.html`의 JS가 접근하는 키가 일치하는가 (`choices` vs `options` 같은 이름 불일치 주의)
- [ ] `/api/submit`의 응답 shape과 결과 화면에서 읽는 필드가 일치하는가
- [ ] 빈 카테고리(문항 0개)를 선택했을 때 프론트가 크래시 없이 안내 메시지를 보여주는가

## 검증 방법
1. Grep으로 모든 `.json` 필드명 패턴과 `data_loader.py`/`main.py`의 접근 코드를 함께 추출해 대조한다
2. 가능하면 `python app/main.py`를 실행해 `/api/categories`, `/api/questions/{category}` 응답을 직접 호출하여 실제 shape을 확인한다 (정적 리뷰만으로는 런타임 불일치를 못 잡는다)
3. 발견한 문제는 파일:라인 + 수정 방법을 명시해 보고한다

## 보고 형식
```
## QA 결과

### 통과
- ...

### 실패 (수정 필요)
- [파일:라인] 문제 설명 → 수정 방법

### 경고 (권장)
- ...
```
