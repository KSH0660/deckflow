from pydantic import BaseModel, Field
from typing import Dict, Any, Optional
from datetime import datetime

class CreateDeckRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=5000)
    style: Optional[Dict[str, str]] = None

class CreateDeckResponse(BaseModel):
    deck_id: str
    status: str = "generating"

class DeckStatusResponse(BaseModel):
    deck_id: str
    status: str
    slide_count: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
