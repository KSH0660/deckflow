"""
Orchestration models for deck generation workflow.

These models represent the composition of business objects used during
deck generation and orchestration processes.
"""

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
