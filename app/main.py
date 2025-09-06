from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import router as api_router
from app.core.config import settings
from app.logging import configure_logging


def create_app() -> FastAPI:
    # Configure logging based on settings
    configure_logging(level=settings.log_level, compact=True)

    app = FastAPI(title="DeckFlow", version="0.1.0")
    app.include_router(api_router)

    # CORS: allow configured origins for browser front-ends
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Initialize Prometheus metrics
    instrumentator = Instrumentator()
    instrumentator.instrument(app).expose(app, endpoint="/metrics")

    return app


app = create_app()
