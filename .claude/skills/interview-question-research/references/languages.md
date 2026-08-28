# Scala / Python / Java 조사 가이드

데이터 엔지니어링 맥락에 특화된 언어 문제를 우선한다. 순수 문법 퀴즈는 지양한다.

## 개념 지도

**Scala**
- 함수형 프로그래밍 패턴 (map/flatMap/fold), case class, 패턴 매칭
- implicit (암묵적 변환/파라미터), Future/Await
- Spark와의 상호작용 (RDD의 함수형 API가 Scala 기반인 이유)

**Python**
- GIL(Global Interpreter Lock)이 CPU-bound 멀티스레딩에 미치는 영향
- 제너레이터/이터레이터, 데코레이터, asyncio
- pandas vs PySpark 처리 방식 차이 (단일 머신 vs 분산)
- 메모리 관리, 타이핑(type hints)

**Java**
- JVM 메모리 모델 (heap/stack, young/old generation)
- GC 종류와 대용량 데이터 처리 시 튜닝 포인트
- 동시성 (Thread, ExecutorService), Stream API, 제네릭

## 자주 나오는 함정 포인트

- Python GIL은 CPU-bound 작업의 진짜 병렬성을 막는다 — multiprocessing이나 PySpark로 우회하는 이유를 설명할 수 있어야 한다
- pandas는 단일 머신 메모리에 전체 데이터를 로드하므로 대용량 데이터에서는 OOM 위험이 있다 — PySpark는 분산 처리로 이를 회피
- Scala의 implicit은 편리하지만 남용하면 코드 추적이 어려워진다 — Spark의 `import spark.implicits._`가 대표적 사용 예
- Java의 GC 튜닝(예: G1GC vs CMS)은 대용량 배치 잡의 처리량과 지연시간 트레이드오프에 직결된다 — Spark executor의 GC 문제와 연결지어 출제 가능

## Spark/JVM 튜닝과의 경계

JVM GC 튜닝이 Spark executor 설정(spark.executor.memory 등)과 겹치는 지점은 `batch-processing.md`와 조율한다. 이 레퍼런스는 언어 자체의 특성에 집중한다.
