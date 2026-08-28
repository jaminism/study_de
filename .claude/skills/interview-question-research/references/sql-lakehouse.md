# Hive / Trino / Iceberg / SQL / ClickHouse 조사 가이드

## 개념 지도

**Hive**
- 메타스토어, 파티셔닝/버켓팅, 외부(external) vs 관리(managed) 테이블
- 파일 포맷 (ORC, Parquet), Hive on Tez/Spark

**Trino**
- 코디네이터/워커 아키텍처, 커넥터 모델(federated query)
- 비용 기반 옵티마이저, 분산 조인 전략 (broadcast vs partitioned)

**Iceberg**
- 테이블 포맷, 스냅샷 격리, 매니페스트 파일, 메타데이터 트리
- 스키마 진화 (컬럼 추가/삭제/타입 변경), hidden partitioning
- 타임트래블, 컴팩션(compaction), 파티션 진화

**SQL**
- 윈도우 함수, 조인 종류와 실행 계획, 인덱스와 쿼리 최적화
- CTE, 정규화/역정규화, 실행 계획(EXPLAIN) 읽기

**ClickHouse**
- MergeTree 엔진 패밀리, 컬럼 지향 저장, 프라이머리 키 vs 정렬 키
- 샤딩/복제, 머티리얼라이즈드 뷰

## 자주 나오는 함정 포인트

- 파티션 프루닝이 실패하는 대표 원인: 파티션 컬럼에 함수를 적용한 WHERE 절 (예: `WHERE YEAR(dt) = 2024`)은 프루닝을 무력화한다
- Iceberg의 hidden partitioning은 사용자가 파티션 컬럼을 직접 WHERE에 명시하지 않아도 프루닝이 동작한다는 점이 Hive와의 핵심 차이
- Hive 메타스토어는 단일 병목이 되기 쉽다 — 대규모 파티션 수 증가 시 쿼리 플래닝이 느려진다
- ClickHouse는 UPDATE/DELETE가 무겁다 (MergeTree는 append-only에 가까움) — OLTP가 아닌 OLAP 워크로드에 맞는 이유를 설명할 수 있어야 한다
- 스키마 진화 시 컬럼 삭제 후 재추가하면 Iceberg는 새 컬럼 ID를 부여해 안전하지만, Hive/Parquet 순수 조합은 컬럼 순서 기반이라 문제가 생길 수 있다

## Spark-Iceberg/Hive 연동 경계

Spark가 Iceberg/Hive 테이블을 읽고 쓰는 지점(카탈로그 연동, 커밋 프로토콜)은 `batch-processing.md`와 겹칠 수 있다 — 이 레퍼런스는 테이블 포맷/쿼리 엔진 자체의 특성에 집중한다.
