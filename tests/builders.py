"""Test data builders for flexible POC testing."""

from app.service.content_creation.models import SlideContent
from app.service.deck_planning.models import (
    ColorTheme,
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)
from app.service.orchestration.models import DeckContext


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
        self._color_theme = ColorTheme.PROFESSIONAL_BLUE
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

    def with_theme(self, theme: ColorTheme):
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
    """Builder for creating flexible SlideContent test data."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._html_content = self._generate_basic_html()
        return self

    def with_html(self, html: str):
        self._html_content = html
        return self

    def with_theme(self, theme: str):
        """Generate HTML with specific theme colors."""
        if theme == "tech_dark":
            self._html_content = self._generate_dark_html()
        elif theme == "professional_blue":
            self._html_content = self._generate_blue_html()
        else:
            self._html_content = self._generate_basic_html()
        return self

    def minimal(self):
        """Create minimal valid HTML content."""
        self._html_content = """
        <!DOCTYPE html>
        <html>
        <head><script src="https://cdn.tailwindcss.com"></script></head>
        <body class="h-screen"><div>Minimal content</div></body>
        </html>
        """
        return self

    def _generate_basic_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="w-full h-screen flex items-center justify-center bg-gray-100">
            <div class="w-full max-w-4xl h-full max-h-screen mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
                <div class="flex-1 p-6 overflow-hidden flex flex-col justify-center">
                    <h1 class="text-2xl font-bold text-blue-800 mb-4">Test Slide</h1>
                    <p class="text-base text-gray-700">Test content</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_dark_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="w-full h-screen flex items-center justify-center bg-gray-900">
            <div class="w-full max-w-4xl h-full max-h-screen mx-auto bg-gray-800 shadow-lg rounded-lg overflow-hidden">
                <div class="flex-1 p-6 overflow-hidden flex flex-col justify-center">
                    <h1 class="text-2xl font-bold text-cyan-400 mb-4">Tech Slide</h1>
                    <p class="text-base text-gray-300">Dark theme content</p>
                </div>
            </div>
        </body>
        </html>
        """

    def _generate_blue_html(self) -> str:
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="w-full h-screen flex items-center justify-center bg-blue-50">
            <div class="w-full max-w-4xl h-full max-h-screen mx-auto bg-white shadow-lg rounded-lg overflow-hidden">
                <div class="flex-1 p-6 overflow-hidden flex flex-col justify-center">
                    <h1 class="text-2xl font-bold text-blue-900 mb-4">Professional Slide</h1>
                    <p class="text-base text-blue-700">Professional content</p>
                </div>
            </div>
        </body>
        </html>
        """

    def build(self) -> SlideContent:
        return SlideContent(html_content=self._html_content)


class DeckContextBuilder:
    """Builder for creating flexible DeckContext test data."""

    def __init__(self):
        self.reset()

    def reset(self):
        self._deck_title = "Test Deck"
        self._audience = "Test Users"
        self._core_message = "Test Message"
        self._goal = "inform"
        self._color_theme = "professional_blue"
        return self

    def with_title(self, title: str):
        self._deck_title = title
        return self

    def with_audience(self, audience: str):
        self._audience = audience
        return self

    def with_theme(self, theme: str):
        self._color_theme = theme
        return self

    def from_deck_plan(self, deck_plan: DeckPlan):
        """Create context from existing deck plan."""
        self._deck_title = deck_plan.deck_title
        self._audience = deck_plan.audience
        self._core_message = deck_plan.core_message
        self._goal = deck_plan.goal.value
        self._color_theme = deck_plan.color_theme.value
        return self

    def build(self) -> DeckContext:
        return DeckContext(
            deck_title=self._deck_title,
            audience=self._audience,
            core_message=self._core_message,
            goal=self._goal,
            color_theme=self._color_theme,
        )


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


def any_deck_context(**overrides) -> DeckContext:
    """Create any valid deck context with optional overrides."""
    builder = DeckContextBuilder()
    for key, value in overrides.items():
        if hasattr(builder, f"with_{key}"):
            getattr(builder, f"with_{key}")(value)
    return builder.build()


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
