PORT ?= 8000
LIMIT ?= 10
BASE ?= http://localhost:$(PORT)
PROMPT ?= Sample deck about AI-driven product roadmap
DECK ?=
OUT ?=
LAYOUT ?= widescreen
EMBED ?= iframe

.PHONY: dev streamlit pre-commit test deck-list deck-create deck-create-id deck-status deck-status-watch deck-cancel deck-export-html deck-export-pdf

# dev server
dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)

# streamlit
streamlit:
	uv run streamlit run streamlit_app.py

# pre-commit
pre-commit:
	uv run pre-commit run --all-files

# tests
test:
	uv run pytest -v --tb=short

# curl helpers
deck-list:
	curl -sS "$(BASE)/api/decks?limit=$(LIMIT)" | uv run python -m json.tool

# create a new deck (background job)
deck-create:
	curl -sS -X POST "$(BASE)/api/decks" \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt": "$(PROMPT)"}' | uv run python -m json.tool

# create a new deck and print only deck_id
deck-create-id:
	@curl -sS -X POST "$(BASE)/api/decks" \
	  -H 'Content-Type: application/json' \
	  -d '{"prompt": "$(PROMPT)"}' \
	  | uv run python -c 'import sys,json; print(json.load(sys.stdin)["deck_id"])'

# get deck status (requires DECK=<deck_id>)
deck-status:
	@[ -n "$(DECK)" ] || (echo "Usage: make deck-status DECK=<deck_id> [PORT=$(PORT)]"; exit 1)
	curl -sS "$(BASE)/api/decks/$(DECK)" | uv run python -m json.tool

# watch deck status until completion
deck-status-watch:
	@[ -n "$(DECK)" ] || (echo "Usage: make deck-status-watch DECK=<deck_id> [PORT=$(PORT)]"; exit 1)
	@echo "Watching deck $(DECK) on $(BASE)..."
	@while true; do \
	  RESP=$$(curl -sS "$(BASE)/api/decks/$(DECK)"); \
	  echo $$RESP | uv run python -m json.tool; \
	  STATUS=$$(echo $$RESP | uv run python -c 'import sys,json; print(json.load(sys.stdin).get("status",""))'); \
	  [ "$$STATUS" = "completed" ] && break; \
	  sleep 2; \
	done

# cancel deck (requires DECK=<deck_id>)
deck-cancel:
	@[ -n "$(DECK)" ] || (echo "Usage: make deck-cancel DECK=<deck_id> [PORT=$(PORT)]"; exit 1)
	curl -sS -X POST "$(BASE)/api/decks/$(DECK)/cancel" | uv run python -m json.tool
