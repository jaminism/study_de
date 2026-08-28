# Spark / Spark Streaming / Hadoop / HDFS 조사 가이드

## 개념 지도

**Spark**
- RDD vs DataFrame vs Dataset, Catalyst 옵티마이저, Tungsten 실행 엔진
- 셔플 (shuffle), 파티셔닝 전략, 데이터 스큐와 salting
- 브로드캐스트 조인 vs 셔플 조인, AQE(Adaptive Query Execution)
- 캐싱/persist 레벨 (MEMORY_ONLY, MEMORY_AND_DISK 등), lazy evaluation, DAG
- 드라이버/익스큐터 구조, speculative execution
- 파티션 수와 셔플 파티션(spark.sql.shuffle.partitions) 튜닝

**Spark Streaming / Structured Streaming**
- 마이크로배치 vs 컨티뉴어스 프로세싱
- 워터마크(watermarking), 체크포인트, 상태 저장(stateful) 연산
- 트리거 종류 (once, fixed interval, continuous), exactly-once sink

**Hadoop / HDFS**
- NameNode/DataNode, 블록 크기, 리플리케이션, 랙 어웨어니스
- HDFS HA(고가용성), small file problem
- MapReduce 기본 흐름 (map → shuffle → reduce)

## 자주 나오는 함정 포인트

- 데이터 스큐는 특정 키에 데이터가 몰릴 때 발생 — salting이나 AQE의 skew join 최적화로 대응
- 셔플 스필(spill)은 메모리 부족 시 디스크로 넘치는 현상 — executor 메모리와 셔플 파티션 수 조정으로 완화
- lazy evaluation 때문에 액션(action)이 호출되기 전까지 트랜스포메이션은 실행되지 않는다 — 디버깅 시 이 점을 놓치기 쉽다
- small file problem은 HDFS NameNode 메모리 부담을 유발 — 파일 병합(compaction) 전략이 필요
- 워터마크 설정이 너무 짧으면 지연 도착 데이터가 누락되고, 너무 길면 상태 저장 비용이 커진다

## Spark 문제와 Kafka Streams 문제의 경계

이 레퍼런스는 Spark 고유 관점(RDD 계보, 마이크로배치 모델)에 집중한다. 컨슈머 그룹/파티션 관리 등 Kafka 고유 개념은 `kafka-streaming.md`에서 다룬다. YARN 위에서의 리소스 스케줄링 세부사항은 `infra-ops.md`에서 다룬다.
