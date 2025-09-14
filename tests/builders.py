"""Test data builders for flexible POC testing."""

from app.models.enums import ColorPreference, LayoutPreference, PersonaPreference
from app.services.content_creation.css_builder import build_slide_css
from app.services.content_creation.models import SlideContent
from app.services.deck_planning.models import (
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)


class SlidePlanBuilder:
    """Builder for creating flexible SlidePlan test data."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._slide_id = 1
        self._slide_title = "Test Slide"
        self._message = "This is a test message"
        self._layout_type = LayoutType.CONTENT_SLIDE
        self._key_points = ["Point 1", "Point 2"]
        self._data_points = ["Data point 1"]
        self._expert_insights = ["Insight 1"]
        self._supporting_facts = ["Fact 1"]
        self._quantitative_details = ["25% increase"]
        return self

    def with_id(self, slide_id: int):
        self._slide_id = slide_id
        return self

    def with_title(self, title: str):
        self._slide_title = title
        return self

    def with_message(self, message: str):
        self._message = message
        return self

    def with_layout(self, layout: LayoutType):
        self._layout_type = layout
        return self

    def with_key_points(self, points: list[str]):
        self._key_points = points
        return self

    def with_data_points(self, data: list[str]):
        self._data_points = data
        return self

    def minimal(self):
        """Create minimal valid slide plan."""
        self._key_points = []
        self._data_points = []
        self._expert_insights = []
        self._supporting_facts = []
        self._quantitative_details = []
        return self

    def rich_content(self):
        """Create content-rich slide plan."""
        self._key_points = ["Key point 1", "Key point 2", "Key point 3", "Key point 4"]
        self._data_points = ["80% improvement", "50% faster processing"]
        self._expert_insights = ["Industry best practice", "Research shows benefits"]
        self._supporting_facts = ["Case study results", "Benchmark data"]
        self._quantitative_details = ["25% ROI", "100 users", "$1M savings"]
        return self

    def build(self) -> SlidePlan:
        return SlidePlan(
            slide_id=self._slide_id,
            slide_title=self._slide_title,
            message=self._message,
            layout_type=self._layout_type,
            key_points=self._key_points,
            data_points=self._data_points,
            expert_insights=self._expert_insights,
            supporting_facts=self._supporting_facts,
            quantitative_details=self._quantitative_details,
        )


class DeckPlanBuilder:
    """Builder for creating flexible DeckPlan test data."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._deck_title = "Test Presentation"
        self._audience = "Test Audience"
        self._core_message = "Test core message"
        self._goal = PresentationGoal.INFORM
        self._color_theme = ColorPreference.PROFESSIONAL_BLUE
        self._slides = [SlidePlanBuilder().build()]
        return self

    def with_title(self, title: str):
        self._deck_title = title
        return self

    def with_audience(self, audience: str):
        self._audience = audience
        return self

    def with_message(self, message: str):
        self._core_message = message
        return self

    def with_goal(self, goal: PresentationGoal):
        self._goal = goal
        return self

    def with_theme(self, theme: ColorPreference):
        self._color_theme = theme
        return self

    def with_slides(self, slides: list[SlidePlan]):
        self._slides = slides
        return self

    def with_slide_count(self, count: int):
        """Generate multiple slides with unique IDs."""
        self._slides = []
        for i in range(count):
            slide = (
                SlidePlanBuilder().with_id(i + 1).with_title(f"Slide {i + 1}").build()
            )
            self._slides.append(slide)
        return self

    def minimal(self):
        """Create minimal valid deck plan."""
        self._deck_title = "Tests"  # Minimal valid (>= 5 chars)
        self._audience = "Users"  # Minimal valid (>= 5 chars)
        self._core_message = "Basic message"  # Minimal valid (>= 10 chars)
        self._slides = [SlidePlanBuilder().minimal().build()]
        return self

    def rich_content(self):
        """Create content-rich deck plan."""
        self._deck_title = "Comprehensive Business Strategy Presentation"
        self._audience = (
            "C-level executives, department heads, and strategic planning teams"
        )
        self._core_message = "Strategic implementation requires data-driven decisions and stakeholder alignment"
        slides = []
        for i in range(6):  # Optimal slide count
            slide = SlidePlanBuilder().with_id(i + 1).rich_content().build()
            slides.append(slide)
        self._slides = slides
        return self

    def build(self) -> DeckPlan:
        return DeckPlan(
            deck_title=self._deck_title,
            audience=self._audience,
            core_message=self._core_message,
            goal=self._goal,
            color_theme=self._color_theme,
            slides=self._slides,
        )


class SlideContentBuilder:
    """Builder for creating flexible SlideContent test data using real CSS builder."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._layout_type = LayoutType.CONTENT_SLIDE
        self._layout_preference = LayoutPreference.PROFESSIONAL
        self._color_preference = ColorPreference.PROFESSIONAL_BLUE
        self._persona_preference = PersonaPreference.BALANCED
        self._title = "Test Slide"
        self._content = "Test content"
        return self

    def with_html(self, html: str):
        """Override with custom HTML (bypasses CSS builder)."""
        self._custom_html = html
        return self

    def with_layout_type(self, layout_type: LayoutType):
        """Set the layout type for CSS generation."""
        self._layout_type = layout_type
        return self

    def with_theme(self, theme: str):
        """Generate HTML with specific theme colors using real CSS builder."""
        if theme == "tech_dark":
            self._color_preference = ColorPreference.MODERN_GREEN
        elif theme == "professional_blue":
            self._color_preference = ColorPreference.PROFESSIONAL_BLUE
        elif theme == "warm_corporate":
            self._color_preference = ColorPreference.WARM_CORPORATE
        else:
            self._color_preference = ColorPreference.PROFESSIONAL_BLUE
        return self

    def with_preferences(
        self,
        layout_pref: LayoutPreference = None,
        color_pref: ColorPreference = None,
        persona_pref: PersonaPreference = None,
    ):
        """Set specific preferences for CSS generation."""
        if layout_pref:
            self._layout_preference = layout_pref
        if color_pref:
            self._color_preference = color_pref
        if persona_pref:
            self._persona_preference = persona_pref
        return self

    def with_content(self, title: str, content: str):
        """Set slide title and content."""
        self._title = title
        self._content = content
        return self

    def minimal(self):
        """Create minimal valid HTML content using real CSS."""
        self._title = "Minimal"
        self._content = "Minimal content"
        return self

    def _generate_html_with_css(self) -> str:
        """Generate HTML using the real CSS builder."""
        # Generate CSS using the real CSS builder
        custom_css = build_slide_css(
            layout_type=self._layout_type,
            layout_preference=self._layout_preference,
            color_preference=self._color_preference,
            persona_preference=self._persona_preference,
        )

        # Create HTML structure that works with the generated CSS and meets slide requirements
        return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
{custom_css}
    </style>
</head>
<body class="w-100 h-100 d-flex align-items-center justify-content-center">
    <div class="slide-container {self._layout_preference.value} overflow-hidden position-relative">
        <div class="content-layout {self._persona_preference.value}-spacing {self._persona_preference.value}-text h-100">
            <div class="content-header">
                <h1 class="mb-4">{self._title}</h1>
            </div>
            <div class="content-body flex-grow-1 overflow-hidden">
                <p class="lead">{self._content}</p>
            </div>
        </div>
    </div>
</body>
</html>"""

    def build(self) -> SlideContent:
        # Use custom HTML if provided, otherwise generate with CSS builder
        if hasattr(self, "_custom_html"):
            html_content = self._custom_html
        else:
            html_content = self._generate_html_with_css()

        return SlideContent(html_content=html_content)


def build_deck_context(**overrides) -> dict:
    """Create deck context dict with optional overrides."""
    defaults = {
        "deck_title": "Test Deck",
        "audience": "Test Users",
        "core_message": "Test Message",
        "goal": "inform",
        "color_theme": "professional_blue",
    }
    defaults.update(overrides)
    return defaults


# Convenience functions for common patterns
def any_slide_plan(**overrides) -> SlidePlan:
    """Create any valid slide plan with optional overrides."""
    builder = SlidePlanBuilder()
    for key, value in overrides.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)
    return builder.build()


def any_deck_plan(**overrides) -> DeckPlan:
    """Create any valid deck plan with optional overrides."""
    builder = DeckPlanBuilder()
    for key, value in overrides.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)
    return builder.build()


def any_slide_content(**overrides) -> SlideContent:
    """Create any valid slide content with optional overrides."""
    builder = SlideContentBuilder()
    for key, value in overrides.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)
    return builder.build()


def any_deck_context(**overrides) -> dict:
    """Create any valid deck context with optional overrides."""
    return build_deck_context(**overrides)


# Test data variants for different scenarios
def minimal_valid_deck_plan() -> DeckPlan:
    """Minimal deck plan that passes validation."""
    return DeckPlanBuilder().minimal().build()


def optimal_quality_deck_plan() -> DeckPlan:
    """High-quality deck plan for scoring tests."""
    return DeckPlanBuilder().rich_content().build()


def multi_slide_deck_plan(count: int = 5) -> DeckPlan:
    """Deck plan with specified number of slides."""
    return DeckPlanBuilder().with_slide_count(count).build()
