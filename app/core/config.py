from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(slots=True)
class Settings:
    # OpenAI / LLM
    openai_api_key: str | None = None
    openai_base_url: str | None = None
    llm_model: str = "gpt-5-mini"

    # File summarization LLM (separate cheaper model)
    summarization_model: str = "gpt-5-nano"

    # Logging
    log_level: str = "INFO"

    # Repository
    repo: str = "sqlite"  # "sqlite" | "memory"
    sqlite_path: str = "decks.db"

    # Concurrency limits
    max_decks: int = 3
    max_slide_concurrency: int = 3

    # CORS
    cors_origins: list[str] = field(
        default_factory=lambda: [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
        ]
    )


def _to_int(value: str | None, default: int) -> int:
    try:
        return int(value) if value is not None else default
    except ValueError:
        return default


def load_settings() -> Settings:
    s = Settings()
    s.openai_api_key = os.getenv("OPENAI_API_KEY")
    s.openai_base_url = os.getenv("OPENAI_BASE_URL")
    s.llm_model = os.getenv("LLM_MODEL", s.llm_model)
    s.summarization_model = os.getenv("SUMMARIZATION_MODEL", s.summarization_model)
    s.log_level = os.getenv("LOG_LEVEL", s.log_level)
    s.repo = os.getenv("DECKFLOW_REPO", s.repo).lower()
    s.sqlite_path = os.getenv("DECKFLOW_SQLITE_PATH", s.sqlite_path)
    s.max_decks = _to_int(os.getenv("DECKFLOW_MAX_DECKS"), s.max_decks)
    s.max_slide_concurrency = _to_int(
        os.getenv("DECKFLOW_MAX_SLIDE_CONCURRENCY"), s.max_slide_concurrency
    )
    # Parse CORS origins: comma-separated list
    cors_env = os.getenv("DECKFLOW_CORS_ORIGINS")
    if cors_env:
        s.cors_origins = [o.strip() for o in cors_env.split(",") if o.strip()]
    return s


# Module-level singleton for convenience imports
settings = load_settings()
