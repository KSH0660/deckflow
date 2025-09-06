PORT ?= 8000
LIMIT ?= 10
BASE ?= http://localhost:$(PORT)

.PHONY: dev streamlit pre-commit deck-list

# dev server
dev:
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $(PORT)
  
# streamlit
streamlit:
	uv run streamlit run streamlit_app.py

# pre-commit
pre-commit:
	uv run pre-commit run --all-files

# curl helpers
deck-list:
	curl -sS "$(BASE)/api/v1/decks?limit=$(LIMIT)" | python -m json.tool
 
