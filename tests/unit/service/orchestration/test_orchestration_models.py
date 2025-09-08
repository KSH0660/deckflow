"""Tests for orchestration models."""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.service.orchestration.models import DeckContext, GeneratedDeck, Slide
from app.service.content_creation.models import SlideContent


class TestSlide:
    """Tests for Slide composition model."""

    def test_valid_slide_creation(self, sample_slide):
        """Test creating a valid composed slide."""
        assert sample_slide.order == 1
        assert isinstance(sample_slide.content, SlideContent)
        assert isinstance(sample_slide.plan, dict)
        assert sample_slide.content.html_content is not None

    def test_slide_with_plan_data(self, sample_slide_content):
        """Test slide with detailed plan data."""
        plan_data = {
            "slide_id": 2,
            "slide_title": "Advanced Testing",
            "message": "Deep dive into testing strategies",
            "layout_type": "data_visual",
            "key_points": ["Unit tests", "Integration tests", "E2E tests"]
        }
        
        slide = Slide(
            order=2,
            content=sample_slide_content,
            plan=plan_data
        )
        
        assert slide.order == 2
        assert slide.plan["slide_title"] == "Advanced Testing"
        assert len(slide.plan["key_points"]) == 3

    def test_slide_order_validation(self, sample_slide_content):
        """Test slide order can be any positive integer."""
        # Valid orders
        slide1 = Slide(order=1, content=sample_slide_content, plan={})
        slide2 = Slide(order=100, content=sample_slide_content, plan={})
        
        assert slide1.order == 1
        assert slide2.order == 100

    def test_slide_serialization(self, sample_slide):
        """Test slide model serialization."""
        data = sample_slide.model_dump()
        
        assert 'order' in data
        assert 'content' in data
        assert 'plan' in data
        assert data['order'] == 1
        
        # Test deserialization
        new_slide = Slide(**data)
        assert new_slide.order == sample_slide.order
        assert new_slide.content.html_content == sample_slide.content.html_content


class TestGeneratedDeck:
    """Tests for GeneratedDeck composition model."""

    def test_valid_generated_deck_creation(self, sample_generated_deck):
        """Test creating a valid generated deck."""
        assert sample_generated_deck.deck_id is not None
        assert sample_generated_deck.title == "Test Presentation"
        assert sample_generated_deck.status == "completed"
        assert len(sample_generated_deck.slides) == 1
        assert isinstance(sample_generated_deck.created_at, datetime)
        assert isinstance(sample_generated_deck.completed_at, datetime)

    def test_generated_deck_with_multiple_slides(self, sample_slide_content):
        """Test generated deck with multiple slides."""
        slides = []
        for i in range(3):
            plan_data = {"slide_id": i + 1, "slide_title": f"Slide {i + 1}"}
            slide = Slide(
                order=i + 1,
                content=sample_slide_content,
                plan=plan_data
            )
            slides.append(slide)
        
        deck = GeneratedDeck(
            deck_id="test-deck-123",
            title="Multi-Slide Presentation",
            status="completed",
            slides=slides,
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        assert len(deck.slides) == 3
        assert deck.slides[0].order == 1
        assert deck.slides[2].order == 3

    def test_generated_deck_status_values(self, sample_slide):
        """Test different status values for generated deck."""
        statuses = ["generating", "completed", "failed", "cancelled"]
        
        for status in statuses:
            deck = GeneratedDeck(
                deck_id="test-deck",
                title="Test Deck", 
                status=status,
                slides=[sample_slide],
                created_at=datetime.now(),
                completed_at=datetime.now()
            )
            assert deck.status == status

    def test_generated_deck_empty_slides(self):
        """Test generated deck with no slides."""
        deck = GeneratedDeck(
            deck_id="empty-deck",
            title="Empty Deck",
            status="generating",
            slides=[],  # Empty slides list
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        assert len(deck.slides) == 0
        assert deck.status == "generating"

    def test_generated_deck_serialization(self, sample_generated_deck):
        """Test generated deck serialization."""
        data = sample_generated_deck.model_dump()
        
        required_fields = {'deck_id', 'title', 'status', 'slides', 'created_at', 'completed_at'}
        assert set(data.keys()) == required_fields
        
        # Test slides are properly serialized
        assert isinstance(data['slides'], list)
        assert len(data['slides']) == 1
        
        # Test deserialization
        new_deck = GeneratedDeck(**data)
        assert new_deck.deck_id == sample_generated_deck.deck_id
        assert new_deck.title == sample_generated_deck.title


class TestDeckContext:
    """Tests for DeckContext workflow model."""

    def test_valid_deck_context_creation(self, sample_deck_context):
        """Test creating a valid deck context."""
        assert isinstance(sample_deck_context.deck_title, str)
        assert len(sample_deck_context.deck_title) >= 5
        assert isinstance(sample_deck_context.audience, str)
        assert len(sample_deck_context.audience) >= 5
        assert isinstance(sample_deck_context.core_message, str)
        assert isinstance(sample_deck_context.goal, str)
        assert isinstance(sample_deck_context.color_theme, str)

    def test_deck_context_minimal_data(self):
        """Test deck context with minimal data."""
        context = DeckContext(
            deck_title="Basic",
            audience="Users",
            core_message="Message",
            goal="inform",
            color_theme="gray"
        )
        
        assert context.deck_title == "Basic"
        assert context.goal == "inform"

    def test_deck_context_comprehensive_data(self):
        """Test deck context with comprehensive data."""
        context = DeckContext(
            deck_title="Comprehensive Machine Learning Strategy for Enterprise Applications",
            audience="C-level executives, technical directors, and ML engineering teams in Fortune 500 companies",
            core_message="Strategic implementation of ML systems requires balancing business value, technical feasibility, and organizational change management",
            goal="persuade",
            color_theme="professional_blue"
        )
        
        assert len(context.deck_title) > 50
        assert "Fortune 500" in context.audience
        assert context.goal == "persuade"

    def test_deck_context_serialization(self, sample_deck_context):
        """Test deck context serialization."""
        data = sample_deck_context.model_dump()
        
        required_fields = {'deck_title', 'audience', 'core_message', 'goal', 'color_theme'}
        assert set(data.keys()) == required_fields
        
        # Test deserialization
        new_context = DeckContext(**data)
        assert new_context.deck_title == sample_deck_context.deck_title
        assert new_context.goal == sample_deck_context.goal

    def test_deck_context_as_dict_conversion(self, sample_deck_context):
        """Test deck context can be converted to dict for service calls."""
        context_dict = sample_deck_context.model_dump()
        
        # Should be compatible with existing service calls
        assert context_dict["deck_title"] == "Test Presentation"
        assert context_dict["color_theme"] == "professional_blue"
        
        # All values should be strings (as expected by existing code)
        for value in context_dict.values():
            assert isinstance(value, str)


class TestModelInteroperability:
    """Tests for how orchestration models work together."""

    def test_slide_content_integration(self, sample_slide, sample_slide_content):
        """Test that Slide properly integrates SlideContent."""
        assert sample_slide.content == sample_slide_content
        assert sample_slide.content.html_content == sample_slide_content.html_content

    def test_deck_slides_ordering(self, sample_slide_content):
        """Test that slides maintain proper ordering in deck."""
        slides = []
        for i in range(5):
            slide = Slide(
                order=i + 1,
                content=sample_slide_content,
                plan={"slide_id": i + 1}
            )
            slides.append(slide)
        
        deck = GeneratedDeck(
            deck_id="ordered-deck",
            title="Ordered Deck",
            status="completed",
            slides=slides,
            created_at=datetime.now(),
            completed_at=datetime.now()
        )
        
        # Verify ordering
        for i, slide in enumerate(deck.slides):
            assert slide.order == i + 1
            assert slide.plan["slide_id"] == i + 1

    def test_context_to_generation_flow(self, sample_deck_context, sample_slide_content):
        """Test context flows properly through generation pipeline."""
        # Context represents what would be passed between services
        context_dict = sample_deck_context.model_dump()
        
        # This dict should be usable in content generation
        assert "deck_title" in context_dict
        assert "color_theme" in context_dict
        
        # And result in proper slide creation
        slide = Slide(
            order=1,
            content=sample_slide_content,
            plan={"context_used": context_dict["deck_title"]}
        )
        
        assert slide.plan["context_used"] == "Test Presentation"