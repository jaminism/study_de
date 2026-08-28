# ElasticSearch / Kibana 조사 가이드

## 개념 지도

**ElasticSearch**
- 역색인(inverted index), 샤드/레플리카, 매핑(mapping)/애널라이저/토크나이저
- 릴러번스 스코어링 (BM25), 쿼리 컨텍스트 vs 필터 컨텍스트
- 집계(aggregation), 인덱스 라이프사이클 관리(ILM), hot-warm-cold 아키텍처

**Kibana**
- 인덱스 패턴, 대시보드/시각화, 알림(alerting)

## 자주 나오는 함정 포인트

- 매핑 폭발(mapping explosion)은 동적 매핑(dynamic mapping)으로 필드가 무한정 늘어날 때 발생 — strict 매핑이나 필드 수 제한으로 예방
- 과도한 샤딩(over-sharding)은 오히려 성능을 저하시킨다 — 샤드가 너무 많으면 클러스터 상태 관리 오버헤드가 커진다
- 쿼리 컨텍스트는 스코어를 계산하고, 필터 컨텍스트는 캐시되며 스코어 계산이 없다 — 단순 존재 여부 필터링에는 필터 컨텍스트를 써야 성능이 좋다
- 텍스트(text) 타입은 애널라이즈되어 검색용, 키워드(keyword) 타입은 애널라이즈 없이 정확 매칭/집계용 — 용도를 혼동하면 집계가 원하는 대로 동작하지 않는다

## ClickHouse와의 경계

ElasticSearch와 ClickHouse 모두 분석용 스토리지로 비교되곤 한다. 이 레퍼런스는 검색/역색인 관점에 집중하고, 컬럼 지향 분석 쿼리 관점은 `sql-lakehouse.md`에서 다룬다.
