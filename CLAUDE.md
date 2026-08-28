## 하네스: 데이터 엔지니어 학습 문제 프로그램

**목표:** 데이터 엔지니어링 기술 스택(Kafka, Kafka Streams, Spark, Spark Streaming, Hadoop, HDFS, Hive, Trino, Iceberg, SQL, ClickHouse, ElasticSearch, Kibana, Scala, Python, Java, Git, Ranger, YARN, K8S, REST API) 학습 문제를 각 전문가 에이전트가 R&D 기반으로 생성하고, 이를 풀어볼 수 있는 Python 웹앱을 제공한다. 요구사항 원문: `request/main_req.md`.

**트리거:** 학습 문제 생성/갱신, 특정 기술 문제 추가, 웹앱 빌드/수정, QA 검증 등 관련 작업 요청 시 `de-interview-orchestrator` 스킬을 사용하라. 단순 질문은 직접 응답 가능.

**변경 이력:**
| 날짜 | 변경 내용 | 대상 | 사유 |
|------|----------|------|------|
| 2026-08-23 | 초기 구성 — 6개 카테고리 전문가(kafka-streaming, batch-processing, sql-lakehouse, search-observability, language, infra-ops) + app-builder + qa-inspector, 4개 스킬(interview-question-research, quiz-webapp-builder, content-app-qa, de-interview-orchestrator) | 전체 | `request/main_req.md` 요구사항 기반 최초 하네스 구축 |
