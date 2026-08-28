---
name: interview-question-research
description: "데이터 엔지니어링 기술 카테고리(Kafka, Spark, Hadoop, HDFS, Hive, Trino, Iceberg, SQL, ClickHouse, ElasticSearch, Kibana, Scala, Python, Java, Git, Ranger, YARN, K8S, REST API 등)의 면접 문제를 R&D 기반으로 조사하고, 객관식/주관식 문제와 정답·해설을 표준 스키마로 생성한다. '면접 문제 만들어줘', '{기술} 문제 추가해줘', '문제 은행 갱신' 요청 시 반드시 이 스킬을 사용할 것."
---

# 면접 문제 R&D 스킬

데이터 엔지니어 면접 대비 프로그램을 위해, 기술 카테고리별 면접 문제를 조사·생성하는 절차와 출력 스키마를 정의한다.

## 왜 R&D가 필요한가
암기된 지식만으로 문제를 만들면 뻔한 정의 문제에 그친다. 실제 면접에서 나오는 문제는 공식 문서의 설계 의도, 트러블슈팅 블로그의 실전 함정, 버전 변경 이력에서 나온다. WebSearch/WebFetch로 최신 정보를 조사한 뒤 문제를 구성해야 현업 면접의 실제 난이도를 재현할 수 있다.

## 조사 절차

1. **개념 지도 작성** — 담당 기술의 핵심 개념을 나열한다 (예: Kafka → 파티션, 리플리케이션, 컨슈머 그룹, 오프셋, exactly-once)
2. **조사** — WebSearch로 "{기술} interview questions", "{기술} 실무 트러블슈팅", 공식 문서의 아키텍처 섹션을 조사한다. 3개 이상의 출처를 교차 확인한다
3. **선별** — 단순 정의 암기보다 판단력을 요구하는 시나리오 문제를 우선한다. "X란 무엇인가"보다 "X 상황에서 Y를 선택해야 하는 이유는?"이 더 좋은 문제다
4. **난이도 배분** — basic 30% / intermediate 45% / advanced 25% 비율을 목표로 한다
5. **작성** — 아래 스키마에 맞춰 MCQ와 주관식을 작성한다
6. **자체 검증** — MCQ는 오답 선택지도 그럴듯해야 한다 (명백히 틀린 선택지 금지). 주관식은 모범 답안과 핵심 키워드를 함께 작성한다

## 출력 스키마

각 기술 카테고리마다 `data/questions/{category}.json` 파일에 아래 구조의 JSON 배열을 저장한다.

**MCQ 형식 규칙 (2026-08-26부터 전 카테고리 공통 필수):** 모든 MCQ는 "다음 중 틀린 것은?" 방식으로 작성한다. `choices` 4개 중 3개는 정확한 설명, `answer_index`가 가리키는 1개만 틀린 설명이어야 한다. "옳은 것을 고르시오" 방식(정답 1개만 맞고 나머지 3개가 틀림)은 금지. 이 조건에서도 오답(=정답으로 헷갈릴 만한 정확한 설명 3개)이 그럴듯해야 하고, `answer_index`가 가리키는 틀린 설명은 명백한 오타나 터무니없는 말이 아니라 실제로 헷갈릴 만한 미묘한 오류여야 한다.

```json
[
  {
    "id": "kafka-mcq-001",
    "category": "kafka",
    "type": "mcq",
    "difficulty": "basic",
    "question": "Kafka에서 파티션 리더가 다운되었을 때 발생하는 일로 틀린 것은?",
    "choices": [
      "ISR 내 팔로워 중 하나가 새 리더로 선출된다",
      "ISR 밖의 복제본은 unclean leader election을 허용하지 않는 한 리더로 선출되지 않는다",
      "리더 재선출이 완료될 때까지 해당 파티션의 쓰기는 일시적으로 지연될 수 있다",
      "해당 파티션의 모든 데이터가 즉시 유실된다"
    ],
    "answer_index": 3,
    "explanation": "ISR(In-Sync Replicas) 내 팔로워 중 하나가 새 리더로 선출되어 가용성을 유지하므로 데이터가 즉시 유실되지는 않는다. ISR 밖의 복제본은 데이터 최신성이 보장되지 않아 unclean leader election을 허용하지 않는 한 리더로 선출되지 않으며, 재선출이 완료되기 전까지는 해당 파티션 쓰기가 일시적으로 지연될 수 있다."
  },
  {
    "id": "kafka-sub-001",
    "category": "kafka",
    "type": "subjective",
    "difficulty": "intermediate",
    "question": "Kafka 컨슈머 그룹에서 리밸런싱이 잦게 발생할 때 원인과 해결 방법을 설명하라.",
    "model_answer": "리밸런싱은 컨슈머 추가/제거, session.timeout.ms 내 heartbeat 실패, max.poll.interval.ms 초과(처리 지연) 등으로 발생한다. 해결책으로는 max.poll.records를 낮춰 처리 시간을 단축하거나, cooperative sticky assignor를 사용해 리밸런싱 범위를 최소화하는 방법이 있다.",
    "keywords": ["session.timeout.ms", "max.poll.interval.ms", "cooperative sticky assignor", "리밸런싱"],
    "explanation": "리밸런싱 자체는 정상 동작이지만, 빈번하면 처리 지연이나 설정 문제를 의심해야 한다."
  }
]
```

**필드 규칙:**
- `id`: `{category}-{mcq|sub}-{순번3자리}` 형식, category 내 유일해야 한다
- `category`: kebab-case, 파일명과 동일 (예: `kafka-streams`, `rest-api`)
- `choices`: MCQ는 정확히 4개, 정답은 `answer_index`(0부터)로 지정
- `keywords`: 주관식 채점 시 핵심 키워드 매칭에 사용 — 3~5개
- 모든 문항에 `explanation` 필수 — 정답 근거를 설명

## 카테고리별 조사 지침

담당 카테고리에 따라 아래 레퍼런스를 로드한다. 각 파일은 해당 카테고리군의 핵심 개념 지도와 자주 나오는 함정 포인트를 담고 있다.

| 카테고리군 | 레퍼런스 |
|-----------|---------|
| Kafka, Kafka Streams | `references/kafka-streaming.md` |
| Spark, Spark Streaming, Hadoop, HDFS | `references/batch-processing.md` |
| Hive, Trino, Iceberg, SQL, ClickHouse | `references/sql-lakehouse.md` |
| ElasticSearch, Kibana | `references/search-observability.md` |
| Scala, Python, Java | `references/languages.md` |
| Git, Ranger, YARN, K8S, REST API | `references/infra-ops.md` |

## 목표 문항 수

카테고리(개별 기술)당 최소 MCQ 10개 + 주관식 5개.

**심화 카테고리 (2026-08-26부터, 총 50문항 이상 필수):** Hive, Spark, Kafka, Kafka Streams, Spark Streaming, SQL, Trino, Iceberg, ClickHouse, ElasticSearch — 이 10개 카테고리는 R&D를 통해 카테고리당 총 50문항 이상(예: MCQ 32개 + 주관식 18개 등 합계 50 이상 비율은 자유)을 생성한다. 개념 중복 없이 50문항을 채우려면 아키텍처 세부 동작, 버전별 변경 이력, 실전 트러블슈팅 시나리오, 설정 파라미터별 함정까지 폭넓게 조사해야 한다.

## 재실행 시 동작

기존 `data/questions/{category}.json`이 있으면 먼저 Read하여 문항을 파악한다. 사용자가 "추가"를 요청하면 기존 `id`와 겹치지 않게 이어서 작성한다. "개선"을 요청하면 지적된 문항만 수정하고 나머지는 보존한다.
