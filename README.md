# DeckFlow — 프롬프트로 덱(슬라이드) 자동 생성

- 하나의 프롬프트만으로 고품질 프레젠테이션 덱을 생성합니다. (Plan → Content → Render)
- API 호출 한 번으로 백그라운드 작업을 시작하고, 폴링으로 진행률과 완료 여부를 확인할 수 있습니다.

## 셋업 방법

필수 요구사항
- Python 3.13 이상
- macOS/Linux/Windows

설치 (uv 권장)
1) uv 설치 (없다면)
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- Windows(Powershell): `iwr https://astral.sh/uv/install.ps1 -UseBasicParsing | iex`

2) 의존성 설치
- `uv sync`

3) 선택: PDF 내보내기(스타일 유지)를 위한 Playwright(Chromium) 설치
- `uv run python -m playwright install chromium`

환경 변수 (선택)
- 저장소 백엔드: `DECKFLOW_REPO=sqlite|memory` (기본: sqlite)
- SQLite 파일 경로: `DECKFLOW_SQLITE_PATH=decks.db`
- 동시성 제한: `DECKFLOW_MAX_DECKS=3` (동시 덱 생성 수), `DECKFLOW_MAX_SLIDE_CONCURRENCY=3` (덱 내 동시 슬라이드 수)

실행
- API 서버: `make dev` (기본 포트 8000)
- Streamlit 앱: `make streamlit`

## 덱 생성 요청 및 폴링

1) 덱 생성 시작 (백그라운드)
- 엔드포인트: `POST /api/v1/decks`
- 바디 예시: `{ "prompt": "AI 제품 로드맵 제안 발표" }`

예시 (curl)
```
curl -sS -X POST \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "AI 제품 로드맵 제안 발표"}' \
  http://localhost:8000/api/v1/decks
```
응답 예시
```
{ "deck_id": "...", "status": "generating" }
```

2) 진행 상태 폴링
- 엔드포인트: `GET /api/v1/decks/{deck_id}`
- 응답: `status`, `progress(%)`, `step`, `slide_count`, `created_at` 등

3) 목록 조회
- 엔드포인트: `GET /api/v1/decks?limit=10`

## Make 명령어

- `make dev` — FastAPI 서버 실행 (PORT 변경 가능)
- `make streamlit` — Streamlit 앱 실행
- `make pre-commit` — 코드 스타일 검사/정리
- `make deck-list` — 최근 덱 목록 조회 (`LIMIT`, `PORT` 조절)

덱 생성/조회/내보내기 헬퍼
- `make deck-create PROMPT="..."` — 덱 생성 시작(백그라운드)
- `make -s deck-create-id PROMPT="..."` — deck_id만 출력
- `make deck-status DECK=<deck_id>` — 상태 조회
- `make deck-status-watch DECK=<deck_id>` — 완료될 때까지 2초 간격 폴링

변수
- `PORT` 기본 8000, `LIMIT` 기본 10
- `PROMPT` 생성 요청 프롬프트 문자열
- `DECK` 대상 deck_id, `OUT` 출력 파일명
- `LAYOUT` `widescreen|a4|a4-landscape`, `EMBED` `iframe|inline`

## 기술 스택

- API: FastAPI, Pydantic
- LLM: LangChain + LiteLLM (모델 연동)
- 저장소: SQLite(aiosqlite) 또는 인메모리
- 프론트: Streamlit (미리보기/다운로드)
- 로깅: structlog
- Export: Playwright(Chromium) 또는 WeasyPrint/wkhtmltopdf (선택)
