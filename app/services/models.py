"""
Orchestration models for deck generation workflow.

These models represent the composition of business objects used during
deck generation and orchestration processes.
"""

from datetime import datetime

from pydantic import BaseModel

from app.services.content_creation.models import SlideContent


class Slide(BaseModel):
    """
    A composed slide with content and plan data.

    This represents a slide after content generation has been applied
    to the slide plan, combining the generated content with the original
    planning data.
    """

    order: int  # Position in presentation (1-based)
    content: SlideContent  # Generated slide content
    plan: dict  # Original slide plan data (flexible dict for compatibility)


class GeneratedDeck(BaseModel):
    """
    Complete generated deck with all slides and metadata.

    This represents the final output of the deck generation process,
    containing all composed slides and deck-level information.
    """

    deck_id: str
    title: str
    status: str  # "generating", "completed", "failed", "cancelled"
    slides: list[Slide]
    created_at: datetime
    completed_at: datetime


class DeckContext(BaseModel):
    """
    Context data passed between orchestration services.

    This provides consistent deck-level context across all slide
    generation operations, ensuring coherent themes and messaging.
    """

    deck_title: str
    audience: str
    core_message: str
    goal: str  # "inform", "persuade", "entertain", etc.
    color_theme: str
