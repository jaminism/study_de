# 진행 상황 기록 (2026-08-25 최종)

## 완료

- **하네스 구성**: 에이전트 8개, 스킬 4개, CLAUDE.md 포인터 등록
- **문제 은행**: 21개 카테고리 전체, 총 420문항 (`data/questions/*.json`)
  - 최초 R&D 생성(347문항) + `docs/reference_01.txt`(사용자의 예전 Gemini 면접 준비 대화 로그) 참고 보강(+73문항, hive/sql/clickhouse/kafka/kafka-streams/spark/spark-streaming/elasticsearch/scala/python)
  - 보강 시 기술 간 "연결 질문"(예: Hive Tez vs Spark 엔진, Kafka Streams vs Spark Structured Streaming, ES vs ClickHouse)은 가장 관련 깊은 단일 카테고리에 편입, category 필드는 단일값 유지
- **Flask 웹앱** (`app/`): main.py, data_loader.py, templates/, static/, requirements.txt — `python app/main.py`로 실행
- **QA 검증**: 통과 19 / 실패 0(수정 완료) / 경고 6 (`_workspace/qa_report.md`)
  - 수정된 버그: 주관식 채점 토큰 매칭 오류(오답률 57%→0.7%), `/api/submit` 세션 없을 때 정답 유출(fail-open→fail-closed), sql.json keywords 스키마 위반, sql-sub-002 모범답안-키워드 불일치

## 남은 경고 (선택적 후속 작업)

- **WARN-1 (품질, 미해결)**: MCQ 정답 index가 0~1에 91% 편중(특히 index1=55%). 변별력을 위해 개선 권장하나 `choices` 순서와 `answer_index`를 쌍으로 재조정해야 하는 6개 전문가 대상 작업이라 리스크·비용 대비 이번 세션에서는 보류
- WARN-3: `subjective+basic` 조합이 0개인 카테고리 5개 (elasticsearch, java, kibana, python, scala) — 크래시 없음, 안내 메시지로 처리됨
- WARN-2/4/5/6: 경미 (일부 주관식 키워드가 모범답안과 완전히 일치하지 않는 17건, result.html 8지선다 상한, 로더 검증 느슨함 등)

## 참고

- 세션 중 여러 차례 사용 한도(session limit)에 걸림 — 6개 에이전트 병렬 실행이 원인. 이후 순차 실행 + 조사 범위 축소로 안정화
- `/loop` 다이나믹 모드로 무인 순차 진행 (에이전트 1개 완료 → 다음 단계 → fallback 25분 wakeup)
