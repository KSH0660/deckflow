"""Tests for deck generation models."""

import pytest
from pydantic import ValidationError

from app.service.deck_planning.models import (
    ColorTheme,
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)


class TestSlidePlan:
    """Tests for SlidePlan model."""

    def test_valid_slide_plan_creation(self, sample_slide_plan):
        """Test creating a valid slide plan."""
        assert sample_slide_plan.slide_id >= 1
        assert isinstance(sample_slide_plan.slide_title, str)
        assert len(sample_slide_plan.slide_title) >= 3
        assert sample_slide_plan.layout_type in LayoutType
        assert len(sample_slide_plan.key_points) >= 0
        assert len(sample_slide_plan.data_points) >= 0

    def test_slide_plan_validation_slide_id_range(self):
        """Test slide_id validation within valid range."""
        # Valid range
        plan = SlidePlan(
            slide_id=1,
            slide_title="Test Title",
            message="Test message content",
            layout_type=LayoutType.TITLE_SLIDE,
        )
        assert plan.slide_id == 1

        plan = SlidePlan(
            slide_id=200,
            slide_title="Test Title",
            message="Test message content",
            layout_type=LayoutType.TITLE_SLIDE,
        )
        assert plan.slide_id == 200

        # Invalid range
        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=0,  # Too low
                slide_title="Test Title",
                message="Test message content",
                layout_type=LayoutType.TITLE_SLIDE,
            )

        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=201,  # Too high
                slide_title="Test Title",
                message="Test message content",
                layout_type=LayoutType.TITLE_SLIDE,
            )

    def test_slide_plan_title_length_validation(self):
        """Test slide title length validation."""
        # Too short
        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=1,
                slide_title="AB",  # Too short (< 3 chars)
                message="Test message content",
                layout_type=LayoutType.TITLE_SLIDE,
            )

        # Too long
        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=1,
                slide_title="A" * 101,  # Too long (> 100 chars)
                message="Test message content",
                layout_type=LayoutType.TITLE_SLIDE,
            )

    def test_slide_plan_message_length_validation(self):
        """Test message length validation."""
        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=1,
                slide_title="Test Title",
                message="Short",  # Too short (< 10 chars)
                layout_type=LayoutType.TITLE_SLIDE,
            )

    def test_slide_plan_enum_validation(self):
        """Test layout type enum validation."""
        # Valid enum
        plan = SlidePlan(
            slide_id=1,
            slide_title="Test Title",
            message="Test message content",
            layout_type=LayoutType.DATA_VISUAL,
        )
        assert plan.layout_type == LayoutType.DATA_VISUAL

        # Invalid enum (would be caught by Pydantic)
        with pytest.raises(ValidationError):
            SlidePlan(
                slide_id=1,
                slide_title="Test Title",
                message="Test message content",
                layout_type="invalid_layout",  # Not a valid enum
            )

    def test_slide_plan_optional_fields_defaults(self):
        """Test that optional list fields have proper defaults."""
        plan = SlidePlan(
            slide_id=1,
            slide_title="Test Title",
            message="Test message content",
            layout_type=LayoutType.TITLE_SLIDE,
        )

        assert plan.key_points == []
        assert plan.data_points == []
        assert plan.expert_insights == []
        assert plan.supporting_facts == []
        assert plan.quantitative_details == []


class TestDeckPlan:
    """Tests for DeckPlan model."""

    def test_valid_deck_plan_creation(self, sample_deck_plan):
        """Test creating a valid deck plan."""
        assert isinstance(sample_deck_plan.deck_title, str)
        assert len(sample_deck_plan.deck_title) >= 5
        assert sample_deck_plan.goal in PresentationGoal
        assert sample_deck_plan.color_theme in ColorTheme
        assert len(sample_deck_plan.slides) >= 1

    def test_deck_plan_title_validation(self):
        """Test deck title validation."""
        # Too short
        with pytest.raises(ValidationError):
            DeckPlan(
                deck_title="Test",  # Too short (< 5 chars)
                audience="Test audience",
                core_message="Test core message",
                goal=PresentationGoal.INFORM,
                color_theme=ColorTheme.PROFESSIONAL_BLUE,
                slides=[],
            )

        # Too long
        with pytest.raises(ValidationError):
            DeckPlan(
                deck_title="A" * 121,  # Too long (> 120 chars)
                audience="Test audience",
                core_message="Test core message",
                goal=PresentationGoal.INFORM,
                color_theme=ColorTheme.PROFESSIONAL_BLUE,
                slides=[],
            )

    def test_deck_plan_audience_validation(self):
        """Test audience validation."""
        with pytest.raises(ValidationError):
            DeckPlan(
                deck_title="Test Title",
                audience="Test",  # Too short (< 5 chars)
                core_message="Test core message",
                goal=PresentationGoal.INFORM,
                color_theme=ColorTheme.PROFESSIONAL_BLUE,
                slides=[],
            )

    def test_deck_plan_core_message_validation(self):
        """Test core message validation."""
        with pytest.raises(ValidationError):
            DeckPlan(
                deck_title="Test Title",
                audience="Test audience",
                core_message="Short",  # Too short (< 10 chars)
                goal=PresentationGoal.INFORM,
                color_theme=ColorTheme.PROFESSIONAL_BLUE,
                slides=[],
            )

    def test_deck_plan_enum_validation(self):
        """Test enum field validation."""
        # Valid enums
        plan = DeckPlan(
            deck_title="Test Title",
            audience="Test audience",
            core_message="Test core message",
            goal=PresentationGoal.PERSUADE,
            color_theme=ColorTheme.TECH_DARK,
            slides=[],
        )
        assert plan.goal == PresentationGoal.PERSUADE
        assert plan.color_theme == ColorTheme.TECH_DARK


class TestEnums:
    """Tests for enum definitions."""

    def test_presentation_goal_values(self):
        """Test PresentationGoal enum values."""
        assert PresentationGoal.PERSUADE == "persuade"
        assert PresentationGoal.INFORM == "inform"
        assert PresentationGoal.INSPIRE == "inspire"
        assert PresentationGoal.EDUCATE == "educate"

    def test_layout_type_values(self):
        """Test LayoutType enum values."""
        assert LayoutType.TITLE_SLIDE == "title_slide"
        assert LayoutType.CONTENT_SLIDE == "content_slide"
        assert LayoutType.COMPARISON == "comparison"
        assert LayoutType.DATA_VISUAL == "data_visual"

    def test_color_theme_values(self):
        """Test ColorTheme enum values."""
        assert ColorTheme.PROFESSIONAL_BLUE == "professional_blue"
        assert ColorTheme.CORPORATE_GRAY == "corporate_gray"
        assert ColorTheme.TECH_DARK == "tech_dark"
