"""Tests for deck planning logic."""

import pytest

from app.service.deck_planning.models import (
    ColorTheme,
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)
from app.service.deck_planning.planner import (
    _calculate_plan_score,
    _get_grade,
    _validate_plan_quality,
    plan_deck,
)
from tests.builders import (
    any_deck_plan,
)


class TestPlanDeck:
    """Tests for main plan_deck function."""

    @pytest.mark.asyncio
    async def test_plan_deck_success(self, mock_llm):
        """Test successful deck planning."""
        deck_plan = any_deck_plan(title="API Testing Presentation")
        mock_llm.generate_structured.return_value = deck_plan

        result = await plan_deck("Create a presentation about API testing", mock_llm)

        assert isinstance(result, DeckPlan)
        assert result.deck_title == "API Testing Presentation"
        assert len(result.slides) >= 1
        mock_llm.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_plan_deck_empty_prompt(self, mock_llm):
        """Test plan_deck with empty prompt."""
        with pytest.raises(ValueError, match="발표 요청은 필수입니다"):
            await plan_deck("", mock_llm)

        with pytest.raises(ValueError, match="발표 요청은 필수입니다"):
            await plan_deck("   ", mock_llm)

    @pytest.mark.asyncio
    async def test_plan_deck_llm_error(self, mock_llm):
        """Test plan_deck when LLM fails."""
        mock_llm.generate_structured.side_effect = Exception("LLM Error")

        with pytest.raises(RuntimeError, match="덱 플랜 생성에 실패했습니다"):
            await plan_deck("Test prompt", mock_llm)

    @pytest.mark.asyncio
    async def test_plan_deck_prompt_formatting(self, mock_llm, sample_deck_plan):
        """Test that prompt is properly formatted."""
        mock_llm.generate_structured.return_value = sample_deck_plan

        await plan_deck("Create AI presentation", mock_llm)

        # Check that the prompt was enhanced
        call_args = mock_llm.generate_structured.call_args
        assert call_args is not None
        prompt = call_args[0][0]  # First positional argument
        assert "Create AI presentation" in prompt
        assert (
            "EXPERT_DATA_STRATEGIST_PROMPT" in prompt
            or "presentation strategist" in prompt.lower()
        )


class TestPlanScoring:
    """Tests for plan quality scoring system."""

    def test_calculate_plan_score_optimal(self):
        """Test scoring for optimal deck plan."""
        # Create optimal deck plan
        slides = []
        for i in range(6):  # Optimal slide count (5-8)
            slide = SlidePlan(
                slide_id=i + 1,
                slide_title="Great slide title for testing",  # Good length
                message="This is a detailed message for testing purposes",
                layout_type=LayoutType.CONTENT_SLIDE,
                key_points=["Point 1", "Point 2", "Point 3", "Point 4"],  # 3-5 optimal
                data_points=["Data 1", "Data 2"],
                expert_insights=["Insight 1", "Insight 2"],
                supporting_facts=["Fact 1", "Fact 2"],
                quantitative_details=["25%", "100 users", "$1M"],
            )
            slides.append(slide)

        plan = DeckPlan(
            deck_title="Comprehensive Test Presentation Title",  # Good length
            audience="Software developers and technical leads working on complex systems",  # Good length
            core_message="This is a comprehensive core message for our testing scenario",
            goal=PresentationGoal.EDUCATE,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=slides,
        )

        score = _calculate_plan_score(plan)

        assert score["total"] > 80  # Should be high quality
        assert score["structure"] > 15
        assert score["content"] > 20
        assert score["data_richness"] > 15
        assert score["clarity"] > 10

    def test_calculate_plan_score_minimal(self):
        """Test scoring for minimal deck plan."""
        slide = SlidePlan(
            slide_id=1,
            slide_title="Min",  # Minimal length
            message="Minimal msg ok",  # Minimal but valid length (>= 10)
            layout_type=LayoutType.TITLE_SLIDE,
            # No optional fields filled
        )

        plan = DeckPlan(
            deck_title="Tests",  # Minimal but valid length (>= 5)
            audience="Users",  # Minimal but valid length (>= 5)
            core_message="Basic message ok",  # Minimal but valid length (>= 10)
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.MINIMAL_MONOCHROME,
            slides=[slide],
        )

        score = _calculate_plan_score(plan)

        assert score["total"] < 50  # Should be low quality
        assert score["structure"] < 15
        assert score["content"] < 20
        assert score["data_richness"] < 10

    def test_get_grade_ranges(self):
        """Test grade assignment for different score ranges."""
        assert "A+ (최우수)" in _get_grade(95)
        assert "A (우수)" in _get_grade(85)
        assert "B+ (양호)" in _get_grade(75)
        assert "B (보통)" in _get_grade(65)
        assert "C+ (미흡)" in _get_grade(55)
        assert "C (개선 필요)" in _get_grade(45)

    def test_get_grade_boundaries(self):
        """Test grade boundaries."""
        assert "A+ (최우수)" in _get_grade(90)
        assert "A (우수)" in _get_grade(80)
        assert "B+ (양호)" in _get_grade(70)
        assert "B (보통)" in _get_grade(60)
        assert "C+ (미흡)" in _get_grade(50)
        assert "C (개선 필요)" in _get_grade(49)


class TestPlanValidation:
    """Tests for plan validation logic."""

    def test_validate_plan_quality_warnings(self, sample_deck_plan, caplog):
        """Test validation warnings for edge cases."""
        # Test with too few slides
        few_slides_plan = DeckPlan(
            deck_title="Test Title",
            audience="Test Audience",
            core_message="Test Message",
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=sample_deck_plan.slides[:2],  # Only 2 slides
        )

        _validate_plan_quality(few_slides_plan)
        # Should log warning but not raise exception

    def test_validate_plan_quality_too_many_slides(self, sample_slide_plan, caplog):
        """Test validation with too many slides."""
        # Create plan with too many slides
        many_slides = [sample_slide_plan] * 15  # 15 slides (> 12)
        for i, slide in enumerate(many_slides):
            slide.slide_id = i + 1

        many_slides_plan = DeckPlan(
            deck_title="Test Title",
            audience="Test Audience",
            core_message="Test Message",
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=many_slides,
        )

        _validate_plan_quality(many_slides_plan)
        # Should log warning but not raise exception

    def test_validate_plan_quality_duplicate_ids(self):
        """Test validation with duplicate slide IDs."""
        slide1 = SlidePlan(
            slide_id=1,
            slide_title="Slide 1",
            message="Test message 1",
            layout_type=LayoutType.TITLE_SLIDE,
        )
        slide2 = SlidePlan(
            slide_id=1,  # Duplicate ID
            slide_title="Slide 2",
            message="Test message 2",
            layout_type=LayoutType.CONTENT_SLIDE,
        )

        plan = DeckPlan(
            deck_title="Test Title",
            audience="Test Audience",
            core_message="Test Message",
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=[slide1, slide2],
        )

        _validate_plan_quality(plan)
        # Should log warning but not raise exception

    def test_validate_plan_quality_empty_slides(self):
        """Test validation with slides missing key points."""
        empty_slide = SlidePlan(
            slide_id=1,
            slide_title="Empty Slide",
            message="This slide has no key points",
            layout_type=LayoutType.CONTENT_SLIDE,
            # key_points will be empty list by default
        )

        plan = DeckPlan(
            deck_title="Test Title",
            audience="Test Audience",
            core_message="Test Message",
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=[empty_slide],
        )

        _validate_plan_quality(plan)
        # Should log warning but not raise exception
