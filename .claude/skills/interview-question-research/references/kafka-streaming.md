# Kafka / Kafka Streams 조사 가이드

## 개념 지도

**Kafka 코어**
- 브로커, 토픽, 파티션, 리플리케이션 팩터
- ISR(In-Sync Replicas), 리더/팔로워, unclean leader election
- 오프셋 관리 (자동/수동 커밋), 컨슈머 그룹, 리밸런싱 (eager vs cooperative sticky)
- 프로듀서 idempotence, 트랜잭션 (exactly-once semantics)
- 로그 세그먼트, 리텐션 정책, 로그 컴팩션
- 처리량 튜닝: batch.size, linger.ms, compression.type
- 스키마 레지스트리 (Avro/Protobuf), 스키마 호환성 모드

**Kafka Streams**
- 토폴로지 (source/processor/sink), DSL vs Processor API
- KStream vs KTable vs GlobalKTable
- 상태 저장소 (RocksDB 기반), changelog 토픽
- 윈도우 연산 (tumbling, hopping, session, sliding)
- 조인 시 co-partitioning 요구사항
- interactive queries, exactly-once processing.guarantee

## 자주 나오는 함정 포인트

- 파티션 수를 늘리면 병렬성은 좋아지지만, 파티션당 오버헤드(파일 핸들, 메모리)와 컨슈머 재조정 비용도 증가한다 — 무조건 늘리는 게 답이 아니다
- 컨슈머 랙(lag)의 원인은 처리 지연뿐 아니라 파티션 불균형, 느린 컨슈머 하나가 전체를 지연시키는 경우도 있다
- unclean leader election을 허용하면 가용성은 높아지지만 데이터 유실 가능성이 생긴다 — 트레이드오프를 이해해야 한다
- Kafka Streams의 상태 저장소는 로컬 디스크(RocksDB)에 있지만 changelog 토픽으로 복제되어 장애 복구가 가능하다는 점이 자주 출제된다
- 리밸런싱 스톰(연쇄 리밸런싱)은 session.timeout.ms를 너무 짧게 설정했을 때 흔히 발생한다

## Kafka Streams vs Spark Streaming 경계

이 레퍼런스는 Kafka 생태계 고유 관점(토픽/파티션/컨슈머 그룹, KTable 상태 관리)에 집중한다. 마이크로배치 대 이벤트 기반 처리 모델의 일반적 비교, Spark Structured Streaming의 워터마크/체크포인트는 `batch-processing.md`에서 다룬다.
