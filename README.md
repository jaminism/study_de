# study_de — 데이터 엔지니어 학습 문제 프로그램

데이터 엔지니어링 기술 스택 학습 문제를 카테고리별로 R&D 기반으로 생성하고, 웹에서 직접 풀어볼 수 있는 Flask 앱입니다.

Kafka, Kafka Streams, Spark, Spark Streaming, Hadoop, HDFS, Hive, Trino, Iceberg, SQL, ClickHouse, Elasticsearch, Kibana, Scala, Python, Java, Git, Ranger, YARN, K8S, REST API — 총 **21개 카테고리, 500문항 이상**.

## 빠른 시작

```bash
pip install -r app/requirements.txt
python app/main.py
```

브라우저에서 http://127.0.0.1:5000 접속. 환경변수로 `HOST`, `PORT`, `SECRET_KEY`, `FLASK_DEBUG`, `LOG_LEVEL` 조정 가능.

## 사용 방법

1. 첫 화면에서 카테고리(전체 또는 개별 기술) · 문제 유형(객관식/주관식) · 난이도(basic/intermediate/advanced) · 문항 수를 선택
2. 문제를 풀면 서버가 즉시 채점 (정답은 서버에서만 보관, 클라이언트로 노출하지 않음)
3. 결과 화면에서 채점 요약과 문항별 해설 확인

객관식은 전 카테고리 공통으로 **"다음 중 틀린 것은?"** 형식입니다 (보기 4개 중 1개만 오답). "옳은 것을 고르시오" 형식은 사용하지 않습니다.

## 프로젝트 구조

```
data/questions/{category}.json   문제 은행 (카테고리별 JSON 배열)
app/main.py                      Flask 라우트 + API
app/data_loader.py               문제 은행 로딩·채점·필터링
app/templates/                   index / quiz / result 화면
.claude/agents/                  카테고리별 전문가 에이전트 (문제 R&D 생성 담당)
.claude/skills/                  오케스트레이터 · 문제 조사 · 웹앱 빌드 · QA 스킬
request/main_req.md              원본 요구사항
```

## 문제 은행 스키마

문항 1건의 공통 필드: `id`, `category`, `type`(`mcq`|`subjective`), `difficulty`(`basic`|`intermediate`|`advanced`), `question`, `explanation`

- **mcq**: `choices`(문자열 4개), `answer_index`(오답의 인덱스)
- **subjective**: `model_answer`, `keywords`(채점용 핵심 키워드 목록)

스키마를 위반한 문항은 파일 전체가 아니라 해당 문항만 건너뜁니다. 카테고리 목록은 하드코딩하지 않고 `data/questions/` 디렉토리를 스캔하므로, JSON 파일만 추가하면 앱 재시작만으로 새 카테고리가 반영됩니다.

## API

| Method | Path | 설명 |
|---|---|---|
| GET | `/api/categories` | 카테고리별 문항 수 |
| GET | `/api/questions/<category>?type=&difficulty=&count=` | 랜덤 N문항 (정답 필드 제외) |
| POST | `/api/submit` | 서버 사이드 채점 (단건/일괄) |
| GET | `/api/health` | 상태 확인 |

## 문제 은행 갱신

새 문제 생성/갱신은 직접 JSON을 편집하지 말고 Claude Code에서 `de-interview-orchestrator` 스킬을 사용하세요. 각 기술 카테고리를 전담하는 전문가 에이전트(`kafka-streaming-expert`, `batch-processing-expert`, `sql-lakehouse-expert`, `search-observability-expert`, `language-expert`, `infra-ops-expert`)가 R&D 기반으로 문제를 조사·작성하고, `qa-inspector`가 스키마·정합성을 검증합니다.
