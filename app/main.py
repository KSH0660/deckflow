from fastapi import FastAPI
from prometheus_fastapi_instrumentator import Instrumentator

from app.api.deck import router as decks_router
from app.core.config import settings
from app.logging import configure_logging


def create_app() -> FastAPI:
    # Configure logging based on settings
    configure_logging(level=settings.log_level, compact=True)

    app = FastAPI(title="DeckFlow", version="0.1.0")
    app.include_router(decks_router, prefix="/api/v1")
    
    # Initialize Prometheus metrics
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")
    
    return app


app = create_app()
