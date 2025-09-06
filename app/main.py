from fastapi import FastAPI

from app.api.deck import router as decks_router
from app.core.config import settings
from app.logging import configure_logging


def create_app() -> FastAPI:
    # Configure logging based on settings
    configure_logging(level=settings.log_level, compact=True)

    app = FastAPI(title="Deck POC")
    app.include_router(decks_router, prefix="/api/v1")
    return app


app = create_app()
