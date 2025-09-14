"""Global pytest configuration and fixtures."""

# Ensure tests never write to the real SQLite DB
# This must be set before any app.* imports so the app picks it up.
import os

os.environ.setdefault("DECKFLOW_REPO", "memory")
os.environ.setdefault("DECKFLOW_SQLITE_PATH", "test-decks.db")

import asyncio
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from app.models.enums import ColorPreference
from app.services.deck_planning.models import (
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)
from app.services.models import Slide
from tests.builders import (
    any_deck_context,
    any_deck_plan,
    any_slide_content,
    any_slide_plan,
)


@pytest.fixture
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm():
    """Mock LLM client for testing."""
    llm = AsyncMock()
    llm.generate_structured = AsyncMock()
    return llm


@pytest.fixture
def mock_repo():
    """Mock repository for testing."""
    repo = AsyncMock()
    repo.save_deck = AsyncMock()
    repo.get_deck = AsyncMock(
        return_value=None
    )  # Default to None for cleaner cancellation checks
    repo.update_deck_status = AsyncMock()
    repo.list_all_decks = AsyncMock()
    return repo


@pytest.fixture
def sample_slide_plan():
    """Sample slide plan for testing - uses builder for flexibility."""
    return any_slide_plan(title="Test Slide Title")


@pytest.fixture
def sample_deck_plan():
    """Sample deck plan for testing - uses builder for flexibility."""
    return any_deck_plan(
        title="Test Presentation",
        audience="Software developers and tech leads",
        message="Testing is essential for reliable software",
    )


@pytest.fixture
def sample_slide_content():
    """Sample slide content for testing - uses builder for flexibility."""
    return any_slide_content()


@pytest.fixture
def sample_slide():
    """Sample composed slide for testing - uses builders for flexibility."""
    slide_content = any_slide_content()
    slide_plan = any_slide_plan()
    return Slide(order=1, content=slide_content, plan=slide_plan.model_dump())


@pytest.fixture
def sample_deck_context():
    """Sample deck context for testing - uses builder for flexibility."""
    return any_deck_context(title="Test Presentation", audience="Software developers")


@pytest.fixture
def sample_generated_deck(sample_slide):
    """Sample generated deck for testing - returns dict format for compatibility."""
    from datetime import datetime

    from app.models.enums import DeckStatus

    return {
        "deck_id": str(uuid4()),
        "title": "Test Presentation",
        "status": DeckStatus.COMPLETED.value,
        "slides": [sample_slide.model_dump()],
        "created_at": datetime.now(),
        "completed_at": datetime.now(),
    }


# Test utilities
def assert_valid_html(html_content: str):
    """Assert that HTML content has basic required elements."""
    assert "<!DOCTYPE html>" in html_content
    assert "<html>" in html_content
    assert "</html>" in html_content
    assert "tailwindcss.com" in html_content


def assert_slide_plan_quality(slide_plan: SlidePlan):
    """Assert slide plan meets quality requirements."""
    assert len(slide_plan.slide_title) >= 3
    assert len(slide_plan.message) >= 10
    assert len(slide_plan.key_points) >= 1
    assert slide_plan.layout_type in LayoutType
    assert slide_plan.slide_id >= 1


def assert_deck_plan_quality(deck_plan: DeckPlan):
    """Assert deck plan meets quality requirements."""
    assert len(deck_plan.deck_title) >= 5
    assert len(deck_plan.audience) >= 5
    assert len(deck_plan.core_message) >= 10
    assert deck_plan.goal in PresentationGoal
    assert deck_plan.color_theme in ColorPreference
    assert len(deck_plan.slides) >= 1
