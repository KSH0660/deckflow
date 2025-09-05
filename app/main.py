from fastapi import FastAPI

from app.api.decks import router as decks_router


def create_app() -> FastAPI:
    app = FastAPI(title="Deck POC")
    app.include_router(decks_router, prefix="/api/v1")
    return app


app = create_app()
