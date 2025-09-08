from datetime import datetime

from pydantic import BaseModel

from app.service.content_creation import SlideContent


# Orchestration composition models - combine data from multiple services
class Slide(BaseModel):
    """Composed slide combining content and planning data"""

    order: int
    content: SlideContent
    plan: dict  # Store slide plan information


class GeneratedDeck(BaseModel):
    """Final generated deck composition"""

    deck_id: str
    title: str
    status: str
    slides: list[Slide]
    created_at: datetime
    completed_at: datetime


class DeckContext(BaseModel):
    """Workflow context shared across services during generation"""

    deck_title: str
    audience: str
    core_message: str
    goal: str
    color_theme: str
