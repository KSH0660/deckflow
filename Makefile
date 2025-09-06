# init
dev:
	uv sync

# streamlit
streamlit:
	uv run streamlit run streamlit_app.py

# pre-commit
pre-commit:
	uv run pre-commit run --all-files