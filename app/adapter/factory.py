import os

from app.adapter.db import InMemoryRepository, SQLiteRepository
from app.adapter.llm.langchain_client import LangchainLLM
from app.core.config import settings
from app.logging import get_logger

logger = get_logger(__name__)


_repo_instance = None


def current_llm(model: str | None = None):
    """Return an LLM client using configured default model.

    Args:
        model: override model name. If None, uses settings.llm_model.
    """
    name = model or settings.llm_model
    return LangchainLLM(model=name)


def current_repo():
    """Return a repository instance based on env settings.

    Env vars:
      - DECKFLOW_REPO: "sqlite" (default) or "memory"
      - DECKFLOW_SQLITE_PATH: path to SQLite DB (default: "decks.db")
    """
    global _repo_instance
    if _repo_instance is not None:
        return _repo_instance

    backend = settings.repo

    if backend == "sqlite":
        db_path = settings.sqlite_path
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
