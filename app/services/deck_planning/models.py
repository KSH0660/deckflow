from pydantic import BaseModel, Field

# Import unified enums
from app.models.enums import LayoutType, PresentationGoal, ColorPreference


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
    color_theme: ColorPreference = Field(description="Visual theme for presentation")
    slides: list[SlidePlan]


# Pure planning models - composition models moved to orchestration
