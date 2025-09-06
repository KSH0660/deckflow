from datetime import datetime

from pydantic import BaseModel, Field


class CreateDeckRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=5000)
    style: dict[str, str] | None = None


class CreateDeckResponse(BaseModel):
    deck_id: str
    status: str = "generating"


class DeckStatusResponse(BaseModel):
    deck_id: str
    status: str
    slide_count: int
    progress: int | None = None
    step: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class DeckListItemResponse(BaseModel):
    deck_id: str
    title: str
    status: str
    slide_count: int
    created_at: datetime
    updated_at: datetime | None = None
