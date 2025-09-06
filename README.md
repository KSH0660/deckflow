# DeckFlow — Prompt-to-Deck Generator

- Goal: Automatically generate high-quality slide decks from a single user prompt (Plan → Template → Render → Edit loop).

- Stack: FastAPI, Pydantic, LangChain (LLM), WebSocket streaming

## Dev Quickstart

- Start API server
  - `make dev` (defaults to port 8000)
  - Override port: `make dev PORT=9000`

- List recent decks via curl
  - `make deck-list` (alias: `make test-deck-list`, `make curl-test`)
  - Override limit/port: `make deck-list LIMIT=5 PORT=8000`

Env configuration
- Repository backend (default sqlite): `DECKFLOW_REPO=sqlite|memory`
- SQLite path (default decks.db): `DECKFLOW_SQLITE_PATH=/path/to/decks.db`
