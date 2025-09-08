from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field


# Enums for deck planning
class PresentationGoal(str, Enum):
    PERSUADE = "persuade"
    INFORM = "inform"
    INSPIRE = "inspire"
    EDUCATE = "educate"


class LayoutType(str, Enum):
    TITLE_SLIDE = "title_slide"
    CONTENT_SLIDE = "content_slide"
    COMPARISON = "comparison"
    DATA_VISUAL = "data_visual"
    PROCESS_FLOW = "process_flow"
    FEATURE_SHOWCASE = "feature_showcase"
    TESTIMONIAL = "testimonial"
    CALL_TO_ACTION = "call_to_action"


class ColorTheme(str, Enum):
    PROFESSIONAL_BLUE = "professional_blue"
    CORPORATE_GRAY = "corporate_gray"
    VIBRANT_PURPLE = "vibrant_purple"
    MODERN_TEAL = "modern_teal"
    ENERGETIC_ORANGE = "energetic_orange"
    NATURE_GREEN = "nature_green"
    ELEGANT_BURGUNDY = "elegant_burgundy"
    TECH_DARK = "tech_dark"
    WARM_SUNSET = "warm_sunset"
    MINIMAL_MONOCHROME = "minimal_monochrome"


# Slide planning models
class SlidePlan(BaseModel):
    slide_id: int = Field(ge=1, le=200, description="Slide sequence id")
    slide_title: str = Field(
        min_length=3, max_length=100, description="Powerful slide title"
    )
    message: str = Field(min_length=10, description="Core one-line message")
    layout_type: LayoutType = Field(
        description="Most suitable layout type for this slide"
    )
    key_points: list[str] = Field(
        default_factory=list, description="Key bullet points (3-5 recommended)"
    )
    data_points: list[str] = Field(
        default_factory=list, description="Statistics, numbers, metrics with context"
    )
    expert_insights: list[str] = Field(
        default_factory=list,
        description="Professional insights, trends, industry facts",
    )
    supporting_facts: list[str] = Field(
        default_factory=list,
        description="Supporting facts, research findings, benchmarks",
    )
    quantitative_details: list[str] = Field(
        default_factory=list,
        description="Specific numbers, percentages, growth rates, comparisons",
    )


class DeckPlan(BaseModel):
    deck_title: str = Field(
        min_length=5, max_length=120, description="Presentation title"
    )
    audience: str = Field(
        min_length=5, description="Target audience and their concerns"
    )
    core_message: str = Field(
        min_length=10, description="Single most important message"
    )
    goal: PresentationGoal = Field(description="Presentation objective")
    color_theme: ColorTheme = Field(description="Visual theme for presentation")
    slides: list[SlidePlan]


# Generated content models
class SlideContent(BaseModel):
    html_content: str


class Slide(BaseModel):
    order: int
    content: SlideContent
    plan: dict  # Store slide plan information


class GeneratedDeck(BaseModel):
    deck_id: str
    title: str
    status: str
    slides: list[Slide]
    created_at: datetime
    completed_at: datetime


# Deck context for generation
class DeckContext(BaseModel):
    deck_title: str
    audience: str
    core_message: str
    goal: str
    color_theme: str