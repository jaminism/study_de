---
name: de-interview-orchestrator
description: "데이터 엔지니어 학습 문제 프로그램(Kafka, Spark, Hadoop, HDFS, Hive, Trino, Iceberg, SQL, ClickHouse, ElasticSearch, Kibana, Scala, Python, Java, Git, Ranger, YARN, K8S, REST API 등) 전체를 조율하는 오케스트레이터. 문제 은행 생성/갱신, 웹앱 빌드, QA 검증을 처리한다. '학습 문제 프로그램 만들어줘', '데이터 엔지니어 학습 하네스 실행', '{기술} 문제 추가/갱신', '문제 은행 다시 생성', '앱 다시 빌드', '결과 개선', 'QA 다시 해줘' 등 초기/후속 요청 모두에 반드시 이 스킬을 사용할 것."
---

# 데이터 엔지니어 학습 문제 프로그램 오케스트레이터

데이터 엔지니어링 학습 문제를 R&D로 생성하고, 이를 풀어볼 수 있는 Python 웹앱을 빌드·검증하는 전체 흐름을 조율하는 통합 스킬.

## 실행 모드: 하이브리드

| Phase | 모드 | 이유 |
|-------|------|------|
| Phase 2~4 (문제 은행 생성) | 에이전트 팀 | 6개 카테고리 전문가가 개념 중복·난이도 일관성을 실시간 조율해야 품질이 높아진다 (팬아웃/팬인) |
| Phase 5 (앱 빌드) | 서브 에이전트 | app-builder 단독 작업, 팀 통신 불필요 |
| Phase 6 (QA 검증) | 서브 에이전트 | qa-inspector 단독 검증, 결과만 리더에게 반환하면 충분 (생성-검증 패턴) |

## 에이전트 구성

| 이름 | 에이전트 타입 | 역할 | 스킬 | 출력 |
|------|-------------|------|------|------|
| kafka-streaming-expert | general-purpose (커스텀 정의) | Kafka, Kafka Streams 문제 R&D | interview-question-research | kafka.json, kafka-streams.json |
| batch-processing-expert | general-purpose (커스텀 정의) | Spark, Spark Streaming, Hadoop, HDFS 문제 R&D | interview-question-research | spark.json, spark-streaming.json, hadoop.json, hdfs.json |
| sql-lakehouse-expert | general-purpose (커스텀 정의) | Hive, Trino, Iceberg, SQL, ClickHouse 문제 R&D | interview-question-research | hive.json, trino.json, iceberg.json, sql.json, clickhouse.json |
| search-observability-expert | general-purpose (커스텀 정의) | ElasticSearch, Kibana 문제 R&D | interview-question-research | elasticsearch.json, kibana.json |
| language-expert | general-purpose (커스텀 정의) | Scala, Python, Java 문제 R&D | interview-question-research | scala.json, python.json, java.json |
| infra-ops-expert | general-purpose (커스텀 정의) | Git, Ranger, YARN, K8S, REST API 문제 R&D | interview-question-research | git.json, ranger.json, yarn.json, k8s.json, rest-api.json |
| app-builder | custom (전체 도구) | 문제 은행을 서빙하는 Flask 웹앱 구현 | quiz-webapp-builder | app/ 디렉토리 전체 |
| qa-inspector | general-purpose (커스텀 정의) | 콘텐츠·앱 통합 정합성 검증 | content-app-qa | _workspace/qa_report.md |

모든 Agent/TeamCreate 호출에는 `model: "opus"`를 명시한다.

## 워크플로우

### Phase 0: 컨텍스트 확인 (후속 작업 지원)

1. `_workspace/` 및 `data/questions/` 존재 여부 확인
2. 실행 모드 결정:
   - **`_workspace/` 및 `data/questions/` 미존재** → 초기 실행. Phase 1로 진행, 21개 전체 카테고리 생성
   - **존재 + 사용자가 특정 기술만 요청** ("카프카 문제만 다시", "SQL 문제 추가해줘") → 부분 재실행. 해당 카테고리를 담당하는 전문가 1명만 서브 에이전트로 재호출 (팀 구성 불필요)
   - **존재 + 앱만 수정 요청** ("결과 화면 고쳐줘") → app-builder만 서브 에이전트로 재호출, Phase 5로 직행
   - **존재 + QA만 요청** ("검증해줘") → qa-inspector만 서브 에이전트로 재호출, Phase 6으로 직행
   - **존재 + 전체 새 실행 요청** → 기존 `_workspace/`를 `_workspace_{YYYYMMDD_HHMMSS}/`로 이동한 뒤 Phase 1 진행 (`data/questions/`, `app/`은 각 에이전트가 재실행 시 스스로 Read 후 개선하므로 보존)
3. 부분 재실행 시: 이전 산출물 경로와 사용자 피드백을 에이전트 프롬프트에 포함하여, 기존 결과를 읽고 반영하도록 지시

### Phase 1: 준비

1. `request/main_req.md`가 존재하면 Read하여 요구 기술 스택과 범위를 재확인한다
2. `_workspace/` 생성 (초기 실행 시)
3. 생성 대상 카테고리 목록 확정 (기본: 요구사항의 21개 기술 전체)

### Phase 2: 콘텐츠 팀 구성

```
TeamCreate(
  team_name: "de-interview-content-team",
  members: [
    { name: "kafka-streaming-expert", agent_type: "kafka-streaming-expert", model: "opus", prompt: "kafka.json, kafka-streams.json 생성. interview-question-research 스킬 사용." },
    { name: "batch-processing-expert", agent_type: "batch-processing-expert", model: "opus", prompt: "spark, spark-streaming, hadoop, hdfs json 생성." },
    { name: "sql-lakehouse-expert", agent_type: "sql-lakehouse-expert", model: "opus", prompt: "hive, trino, iceberg, sql, clickhouse json 생성." },
    { name: "search-observability-expert", agent_type: "search-observability-expert", model: "opus", prompt: "elasticsearch, kibana json 생성." },
    { name: "language-expert", agent_type: "language-expert", model: "opus", prompt: "scala, python, java json 생성." },
    { name: "infra-ops-expert", agent_type: "infra-ops-expert", model: "opus", prompt: "git, ranger, yarn, k8s, rest-api json 생성." }
  ]
)
```

`TaskCreate`로 21개 카테고리 파일 생성을 각 담당 전문가에게 작업으로 등록한다 (전문가 1인당 2~5개 작업).

### Phase 3: 문제 은행 생성

**실행 방식:** 팀원들이 자체 조율

각 전문가는 담당 기술의 `interview-question-research` 스킬을 사용해 R&D를 수행하고 `data/questions/{category}.json`을 작성한다. 개념이 겹치는 경계(예: Kafka Streams ↔ Spark Streaming, YARN ↔ Spark 튜닝)는 각 에이전트 정의의 "팀 통신 프로토콜"에 따라 SendMessage로 조율한다.

리더는 유휴 알림을 모니터링하고, 특정 전문가가 막히면 SendMessage로 상태를 확인한다.

### Phase 4: 통합 검토 및 팀 정리

1. 모든 전문가의 작업 완료 대기 (TaskGet)
2. 리더가 `data/questions/*.json` 21개 파일을 모두 Read하여 개수와 기본 스키마(필수 필드 존재)를 훑어본다 — 정밀 검증은 Phase 6의 qa-inspector가 담당
3. 팀원 종료 요청 후 `TeamDelete`로 팀 정리 (다음 Phase는 서브 에이전트 모드이므로 팀을 반드시 정리)

### Phase 5: 앱 빌드

**실행 방식:** 서브 에이전트

```
Agent(
  subagent_type: "app-builder",
  model: "opus",
  prompt: "data/questions/*.json을 서빙하는 Flask 앱을 app/에 구현. quiz-webapp-builder 스킬 사용."
)
```

app-builder가 `data/questions/`를 Read하여 `app/` 디렉토리를 생성한다.

### Phase 6: QA 검증 (생성-검증 루프)

**실행 방식:** 서브 에이전트

```
Agent(
  subagent_type: "qa-inspector",
  model: "opus",
  prompt: "data/questions/*.json과 app/의 통합 정합성 검증. content-app-qa 스킬 사용. 결과를 _workspace/qa_report.md에 저장."
)
```

1. `_workspace/qa_report.md`를 Read하여 실패 항목 확인
2. 실패 항목이 있으면:
   - 콘텐츠 스키마 문제 → 해당 카테고리 담당 전문가를 서브 에이전트로 재호출, 리포트의 구체적 지적사항 전달
   - 앱 경계면 문제 → app-builder를 서브 에이전트로 재호출, 리포트 전달
3. 재검증 (qa-inspector 재호출), **최대 2회 루프**. 2회 후에도 미해결 항목은 최종 보고서에 명시하고 진행

### Phase 7: 정리 및 보고

1. `_workspace/` 보존 (사후 감사 추적용)
2. 사용자에게 결과 요약: 생성된 카테고리 수, 총 문항 수, 앱 실행 방법(`python app/main.py`), QA 통과/미해결 항목

## 데이터 흐름

```
[리더] → TeamCreate → 6개 카테고리 전문가 ←SendMessage→ 상호 조율
                              │
                              ↓ (각자 Write)
                    data/questions/*.json (21개 파일)
                              │
                              ↓ TeamDelete 후
                    Agent(app-builder) ─Read→ app/ 생성
                              │
                              ↓
                    Agent(qa-inspector) ─Read→ _workspace/qa_report.md
                              │
                    (실패 시) 해당 에이전트 재호출 ─ 최대 2회 루프
                              │
                              ↓
                         최종 보고
```

## 에러 핸들링

| 상황 | 전략 |
|------|------|
| 카테고리 전문가 1명 실패/중지 | 리더가 유휴 알림 감지 → SendMessage로 상태 확인 → 재시작. 재실패 시 해당 카테고리 파일 없이 진행하고 최종 보고에 누락 명시 |
| 전문가 과반 실패 | 사용자에게 알리고 진행 여부 확인 |
| app-builder 실패 | 1회 재시도. 재실패 시 부분 구현 상태를 보고하고 수동 개입 요청 |
| qa-inspector가 앱 실행 불가로 정적 리뷰만 수행 | 결과에 "런타임 미검증" 명시하고 그대로 진행 |
| 2회 QA 루프 후에도 실패 항목 잔존 | 최종 보고서에 미해결 항목을 구체적으로 명시, 삭제하지 않고 다음 실행을 위해 남겨둠 |

## 테스트 시나리오

### 정상 흐름
1. 사용자가 "데이터 엔지니어 학습 문제 프로그램 만들어줘" 요청
2. Phase 1에서 `request/main_req.md`의 21개 기술 확인
3. Phase 2~3에서 6명 팀 구성, 21개 파일 생성 (팀원 간 경계 조율 SendMessage 발생)
4. Phase 4에서 팀 정리
5. Phase 5에서 app-builder가 `app/` 생성
6. Phase 6에서 qa-inspector가 검증, 실패 항목 0건
7. Phase 7에서 "21개 카테고리, 총 N문항, `python app/main.py`로 실행 가능" 보고

### 에러 흐름
1. Phase 3에서 sql-lakehouse-expert가 중지
2. 리더가 유휴 알림 수신, SendMessage로 상태 확인 → 재시작 실패
3. hive/trino/iceberg/sql/clickhouse 5개 카테고리 누락 상태로 Phase 4 진행
4. Phase 5~6은 나머지 16개 카테고리로 정상 진행
5. 최종 보고서에 "SQL/Lakehouse 5개 카테고리 미생성, 재실행 필요" 명시
