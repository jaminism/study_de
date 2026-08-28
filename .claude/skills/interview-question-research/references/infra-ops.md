# Git / Ranger / YARN / K8S / REST API 조사 가이드

## 개념 지도

**Git**
- 브랜치 전략 (git-flow, trunk-based), rebase vs merge, 충돌 해결

**Ranger**
- 정책 기반 접근 제어(RBAC/ABAC), Hadoop 생태계 연동 (Hive/HDFS/Kafka 플러그인)
- 감사 로그(audit log), 정책 전파 지연

**YARN**
- ResourceManager/NodeManager, 컨테이너, 스케줄러 종류 (Capacity Scheduler, Fair Scheduler)
- 큐(queue) 관리와 리소스 할당

**K8S**
- 파드/디플로이먼트/서비스, 리소스 요청(requests)/제한(limits)
- StatefulSet (Kafka/ElasticSearch 등 상태 저장 워크로드 운영)
- Operator 패턴 (예: Spark on K8s Operator), PersistentVolume

**REST API**
- 멱등성(idempotency), 상태 코드 의미, 페이지네이션, 버저닝
- 인증 (OAuth2/JWT), 레이트 리밋

## 자주 나오는 함정 포인트

- YARN 큐 설정이 잘못되면 특정 큐가 리소스를 독점해 다른 잡이 리소스 스타베이션을 겪는다 — Capacity Scheduler의 최소/최대 보장 개념 이해가 핵심
- Ranger 정책 변경은 즉시 반영되지 않고 폴링 주기에 따라 전파 지연이 있을 수 있다
- K8S에서 리소스 limits를 너무 낮게 설정하면 OOMKilled가 발생 — requests와 limits의 차이(스케줄링 기준 vs 실제 제한)를 정확히 알아야 한다
- StatefulSet은 안정적인 네트워크 식별자와 순서 있는 배포/삭제를 보장 — Kafka 브로커처럼 식별자가 중요한 워크로드에 필요한 이유
- REST API의 멱등성은 PUT/DELETE에는 요구되지만 POST는 기본적으로 멱등하지 않다 — 멱등키(idempotency key) 패턴으로 POST도 멱등하게 만들 수 있다

## Spark/Hadoop, Kafka와의 경계

YARN 위에서 Spark/Hadoop 잡이 실행되는 애플리케이션 레벨 튜닝은 `batch-processing.md`에서, K8S 위에서 Kafka를 운영하는 시나리오는 `kafka-streaming.md`와 조율한다. 이 레퍼런스는 인프라/오케스트레이션 레벨 자체에 집중한다.
