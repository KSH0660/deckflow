import os

from app.adapter.db import InMemoryRepository, SQLiteRepository
from app.adapter.llm.langchain_client import LangchainLLM
from app.logging import get_logger


logger = get_logger(__name__)


_repo_instance = None


def current_llm():
    return LangchainLLM()


def current_repo():
    """Return a repository instance based on env settings.

    Env vars:
      - DECKFLOW_REPO: "sqlite" (default) or "memory"
      - DECKFLOW_SQLITE_PATH: path to SQLite DB (default: "decks.db")
    """
    global _repo_instance
    if _repo_instance is not None:
        return _repo_instance

    backend = os.getenv("DECKFLOW_REPO", "sqlite").lower()

    if backend == "sqlite":
        db_path = os.getenv("DECKFLOW_SQLITE_PATH", "decks.db")
        logger.info("Repository initialized", backend=backend, db_path=db_path)
        _repo_instance = SQLiteRepository(db_path=db_path)
    elif backend == "memory":
        logger.info("Repository initialized", backend=backend)
        _repo_instance = InMemoryRepository()
    else:
        logger.warning("Unknown DECKFLOW_REPO; falling back to sqlite", backend=backend)
        db_path = os.getenv("DECKFLOW_SQLITE_PATH", "decks.db")
        _repo_instance = SQLiteRepository(db_path=db_path)

    return _repo_instance
