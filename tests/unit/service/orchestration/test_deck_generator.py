"""Tests for orchestration deck generator workflow."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

from app.service.orchestration.deck_generator import generate_deck
from app.service.orchestration.models import Slide
from tests.builders import (
    DeckPlanBuilder,
    SlideContentBuilder,
    SlidePlanBuilder,
    any_deck_plan,
    any_slide_content,
    multi_slide_deck_plan,
)


class TestGenerateDeck:
    """Tests for main generate_deck orchestration function."""

    @pytest.mark.asyncio
    async def test_generate_deck_success(self, mock_llm, mock_repo):
        """Test successful end-to-end deck generation."""
        deck_id = uuid4()
        
        # Use builders for flexible test data
        deck_plan = any_deck_plan(title="API Testing Presentation")
        slide_content = any_slide_content()
        
        # Mock the planning step
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            # Mock the content generation step
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                result = await generate_deck(
                    prompt="Create a testing presentation",
                    llm=mock_llm,
                    repo=mock_repo,
                    deck_id=deck_id
                )
        
        assert result == str(deck_id)
        
        # Verify repository calls
        mock_repo.save_deck.assert_called()
        save_calls = mock_repo.save_deck.call_args_list
        assert len(save_calls) >= 2  # Initial save + final save
        
        # Check final deck data
        final_call = save_calls[-1]
        final_deck_data = final_call[0][1]  # Second argument (deck data)
        assert final_deck_data["status"] == "completed"
        assert len(final_deck_data["slides"]) == 1

    @pytest.mark.asyncio
    async def test_generate_deck_with_progress_callback(self, mock_llm, mock_repo):
        """Test deck generation with progress tracking."""
        progress_updates = []
        
        async def progress_callback(step: str, progress: int, slide_data=None):
            progress_updates.append((step, progress, slide_data))
        
        # Use builders for flexible test data
        deck_plan = any_deck_plan()
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                await generate_deck(
                    prompt="Test prompt",
                    llm=mock_llm,
                    repo=mock_repo,
                    progress_callback=progress_callback
                )
        
        # Should have multiple progress updates
        assert len(progress_updates) > 3
        
        # Check specific progress stages
        steps = [update[0] for update in progress_updates]
        assert any("Planning" in step for step in steps)
        assert any("Generating" in step or "slide" in step for step in steps)
        assert any("Finalizing" in step for step in steps)

    @pytest.mark.asyncio
    async def test_generate_deck_with_files(self, mock_llm, mock_repo):
        """Test deck generation with uploaded files."""
        files = [
            MagicMock(
                filename="test.txt",
                content_type="text/plain", 
                size=1024,
                extracted_text="This is test file content for the presentation"
            )
        ]
        
        # Use builders for flexible test data
        deck_plan = any_deck_plan(title="File-based Presentation")
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck') as mock_plan:
            mock_plan.return_value = deck_plan
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                await generate_deck(
                    prompt="Create presentation from files",
                    llm=mock_llm,
                    repo=mock_repo,
                    files=files
                )
        
        # Check that enhanced prompt was created with file content
        mock_plan.assert_called_once()
        enhanced_prompt = mock_plan.call_args[0][0]
        assert "Create presentation from files" in enhanced_prompt
        assert "test.txt" in enhanced_prompt
        assert "This is test file content" in enhanced_prompt

    @pytest.mark.asyncio
    async def test_generate_deck_planning_failure(self, mock_llm, mock_repo):
        """Test deck generation when planning fails."""
        with patch('app.service.orchestration.deck_generator.plan_deck', side_effect=Exception("Planning failed")):
            with pytest.raises(Exception, match="Planning failed"):
                await generate_deck(
                    prompt="Test prompt",
                    llm=mock_llm,
                    repo=mock_repo
                )
        
        # Should mark deck as failed
        mock_repo.update_deck_status.assert_called()

    @pytest.mark.asyncio
    async def test_generate_deck_content_generation_failure(self, mock_llm, mock_repo):
        """Test deck generation when content generation fails."""
        deck_plan = any_deck_plan()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', side_effect=Exception("Content failed")):
                with pytest.raises(Exception, match="Content failed"):
                    await generate_deck(
                        prompt="Test prompt",
                        llm=mock_llm,
                        repo=mock_repo
                    )

    @pytest.mark.asyncio
    async def test_generate_deck_cancellation(self, mock_llm, mock_repo):
        """Test deck generation cancellation."""
        # Mock repository to return cancelled status
        mock_repo.get_deck.return_value = {"status": "cancelled"}
        
        # Use builders for flexible test data
        deck_plan = any_deck_plan()
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                result = await generate_deck(
                    prompt="Test prompt",
                    llm=mock_llm,
                    repo=mock_repo
                )
        
        # Should return deck_id even when cancelled
        assert result is not None

    @pytest.mark.asyncio
    async def test_generate_deck_multiple_slides(self, mock_llm, mock_repo):
        """Test deck generation with multiple slides."""
        # Use builder to create flexible multi-slide plan
        deck_plan = multi_slide_deck_plan(count=3)
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                await generate_deck(
                    prompt="Multi-slide test",
                    llm=mock_llm,
                    repo=mock_repo
                )
        
        # Check that all slides were processed
        final_save_call = mock_repo.save_deck.call_args_list[-1]
        final_deck_data = final_save_call[0][1]
        assert len(final_deck_data["slides"]) == 3

    @pytest.mark.asyncio
    async def test_generate_deck_context_creation(self, mock_llm, mock_repo):
        """Test that proper deck context is created for content generation."""
        deck_plan = any_deck_plan(title="Context Test Presentation")
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content) as mock_write:
                await generate_deck(
                    prompt="Context test",
                    llm=mock_llm,
                    repo=mock_repo
                )
        
        # Check that write_content was called with proper context
        mock_write.assert_called()
        call_args = mock_write.call_args
        slide_info = call_args[0][0]  # First arg
        deck_context = call_args[0][1]  # Second arg
        
        # Verify context has expected keys
        expected_keys = {"deck_title", "audience", "core_message", "goal", "color_theme"}
        assert set(deck_context.keys()) == expected_keys
        assert deck_context["deck_title"] == deck_plan.deck_title

    @pytest.mark.asyncio
    async def test_generate_deck_metrics_tracking(self, mock_llm, mock_repo):
        """Test that metrics are properly tracked during generation."""
        deck_plan = any_deck_plan()
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                # Mock the metrics
                with patch('app.service.orchestration.deck_generator.active_deck_generations') as mock_active:
                    with patch('app.service.orchestration.deck_generator.deck_generation_total') as mock_total:
                        with patch('app.service.orchestration.deck_generator.slide_generation_total') as mock_slides:
                            await generate_deck(
                                prompt="Metrics test",
                                llm=mock_llm,
                                repo=mock_repo
                            )
        
        # Verify metrics were called
        mock_active.inc.assert_called()
        mock_active.dec.assert_called()
        mock_total.labels.assert_called_with(status="completed")
        mock_slides.inc.assert_called()

    @pytest.mark.asyncio
    async def test_generate_deck_slide_model_creation(self, mock_llm, mock_repo):
        """Test that Slide models are properly created during orchestration."""
        deck_plan = any_deck_plan()
        slide_content = any_slide_content()
        
        with patch('app.service.orchestration.deck_generator.plan_deck', return_value=deck_plan):
            with patch('app.service.orchestration.deck_generator.write_content', return_value=slide_content):
                await generate_deck(
                    prompt="Slide model test",
                    llm=mock_llm,
                    repo=mock_repo
                )
        
        # Get the final deck data
        final_save_call = mock_repo.save_deck.call_args_list[-1]
        final_deck_data = final_save_call[0][1]
        
        # Verify slide structure
        slides_data = final_deck_data["slides"]
        assert len(slides_data) == 1
        
        slide_data = slides_data[0]
        assert "order" in slide_data
        assert "content" in slide_data
        assert "plan" in slide_data
        assert slide_data["order"] == 1