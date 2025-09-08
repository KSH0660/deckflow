"""Integration tests for full deck generation workflow."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service.content_creation.models import SlideContent
from app.service.deck_planning.models import (
    ColorTheme,
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)
from app.service.orchestration import generate_deck


@pytest.mark.integration
class TestFullDeckWorkflow:
    """Integration tests for complete deck generation workflow."""

    @pytest.mark.asyncio
    async def test_end_to_end_deck_generation(self, mock_llm, mock_repo):
        """Test complete deck generation from prompt to final output."""
        # Mock planning result
        mock_deck_plan = DeckPlan(
            deck_title="Integration Test Presentation",
            audience="QA Engineers and Developers",
            core_message="Integration testing ensures system reliability",
            goal=PresentationGoal.EDUCATE,
            color_theme=ColorTheme.TECH_DARK,
            slides=[
                SlidePlan(
                    slide_id=1,
                    slide_title="Introduction to Integration Testing",
                    message="Integration testing validates component interactions",
                    layout_type=LayoutType.TITLE_SLIDE,
                    key_points=[
                        "System reliability",
                        "Component integration",
                        "Test automation",
                    ],
                    data_points=[
                        "80% of bugs found in integration",
                        "40% faster deployment",
                    ],
                    expert_insights=["Industry best practices", "DevOps integration"],
                    supporting_facts=["Research studies", "Case studies"],
                    quantitative_details=[
                        "50% reduction in production bugs",
                        "2x faster releases",
                    ],
                ),
                SlidePlan(
                    slide_id=2,
                    slide_title="Testing Strategies",
                    message="Multiple strategies ensure comprehensive coverage",
                    layout_type=LayoutType.CONTENT_SLIDE,
                    key_points=["Unit tests", "Integration tests", "E2E tests"],
                    data_points=["Test pyramid ratio", "Coverage metrics"],
                    expert_insights=["Testing best practices"],
                    supporting_facts=["Industry standards"],
                    quantitative_details=["70% unit, 20% integration, 10% E2E"],
                ),
            ],
        )

        # Mock content generation result
        mock_slide_content = SlideContent(
            html_content="""
            <!DOCTYPE html>
            <html>
            <head>
                <script src="https://cdn.tailwindcss.com"></script>
            </head>
            <body class="w-full h-screen flex items-center justify-center bg-gray-900">
                <div class="w-full max-w-4xl h-full max-h-screen mx-auto bg-gray-800 shadow-lg rounded-lg overflow-hidden">
                    <div class="flex-1 p-6 overflow-hidden flex flex-col justify-center">
                        <h1 class="text-2xl font-bold text-cyan-400 mb-4">Integration Test Presentation</h1>
                        <p class="text-base text-gray-300 mb-4">Integration testing validates component interactions</p>
                        <ul class="space-y-2">
                            <li class="text-sm text-gray-300">• System reliability</li>
                            <li class="text-sm text-gray-300">• Component integration</li>
                            <li class="text-sm text-gray-300">• Test automation</li>
                        </ul>
                    </div>
                </div>
            </body>
            </html>
            """
        )

        # Setup mocks with realistic delays
        async def mock_plan_deck(prompt, llm):
            return mock_deck_plan

        async def mock_write_content(slide_info, deck_context, llm):
            return mock_slide_content

        # Mock the service functions
        import app.service.orchestration.deck_generator

        app.service.orchestration.deck_generator.plan_deck = mock_plan_deck
        app.service.orchestration.deck_generator.write_content = mock_write_content

        # Track progress updates
        progress_updates = []

        async def track_progress(step: str, progress: int, slide_data=None):
            progress_updates.append((step, progress, slide_data))

        # Execute full workflow
        result = await generate_deck(
            prompt="Create a comprehensive presentation about integration testing best practices",
            llm=mock_llm,
            repo=mock_repo,
            progress_callback=track_progress,
        )

        # Verify result
        assert result is not None
        assert isinstance(result, str)  # Should be deck_id

        # Verify progress tracking
        assert len(progress_updates) > 0
        progress_values = [update[1] for update in progress_updates]
        assert min(progress_values) >= 0
        assert max(progress_values) <= 100

        # Verify repository interactions
        save_calls = mock_repo.save_deck.call_args_list
        assert len(save_calls) >= 2  # Initial + final save

        # Verify final deck structure
        final_deck = save_calls[-1][0][1]  # Last save call, deck data
        assert final_deck["status"] == "completed"
        assert final_deck["deck_title"] == "Integration Test Presentation"
        assert len(final_deck["slides"]) == 2

        # Verify slide structure
        slide = final_deck["slides"][0]
        assert "order" in slide
        assert "content" in slide
        assert "plan" in slide
        assert slide["content"]["html_content"] is not None

    @pytest.mark.asyncio
    async def test_workflow_with_file_processing(self, mock_llm, mock_repo):
        """Test workflow with file input processing."""
        # Mock file input
        mock_files = [
            MagicMock(
                filename="testing_strategy.pdf",
                content_type="application/pdf",
                size=5120,
                extracted_text="""
                Testing Strategy Document

                1. Unit Testing
                - Test individual components
                - 80% code coverage target
                - Fast execution (< 100ms per test)

                2. Integration Testing
                - Test component interactions
                - Database integration
                - API endpoint testing

                3. End-to-End Testing
                - User workflow validation
                - Cross-browser testing
                - Performance validation
                """,
            )
        ]

        # Setup basic mocks
        mock_deck_plan = DeckPlan(
            deck_title="File-Based Testing Strategy",
            audience="Development Team",
            core_message="Structured testing approach ensures quality",
            goal=PresentationGoal.INFORM,
            color_theme=ColorTheme.PROFESSIONAL_BLUE,
            slides=[
                SlidePlan(
                    slide_id=1,
                    slide_title="Testing Strategy Overview",
                    message="Comprehensive testing ensures software quality",
                    layout_type=LayoutType.TITLE_SLIDE,
                    key_points=["Unit testing", "Integration testing", "E2E testing"],
                )
            ],
        )

        mock_content = SlideContent(html_content="<html>Mock content</html>")

        # Mock service functions
        import app.service.orchestration.deck_generator

        app.service.orchestration.deck_generator.plan_deck = AsyncMock(
            return_value=mock_deck_plan
        )
        app.service.orchestration.deck_generator.write_content = AsyncMock(
            return_value=mock_content
        )

        # Execute workflow with files
        result = await generate_deck(
            prompt="Create presentation from testing strategy document",
            llm=mock_llm,
            repo=mock_repo,
            files=mock_files,
        )

        assert result is not None

        # Verify enhanced prompt was created with file content
        plan_call = app.service.orchestration.deck_generator.plan_deck.call_args
        enhanced_prompt = plan_call[0][0]
        assert "testing_strategy.pdf" in enhanced_prompt
        assert "Unit Testing" in enhanced_prompt
        assert "Integration Testing" in enhanced_prompt

    @pytest.mark.asyncio
    async def test_workflow_error_recovery(self, mock_llm, mock_repo):
        """Test workflow error handling and recovery."""
        # Setup to fail on first attempt, succeed on retry
        call_count = 0

        async def failing_plan_deck(prompt, llm):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated planning failure")
            return DeckPlan(
                deck_title="Recovery Test",
                audience="Test Audience",
                core_message="Error recovery works",
                goal=PresentationGoal.INFORM,
                color_theme=ColorTheme.CORPORATE_GRAY,
                slides=[
                    SlidePlan(
                        slide_id=1,
                        slide_title="Recovery Success",
                        message="System recovered from error",
                        layout_type=LayoutType.CONTENT_SLIDE,
                    )
                ],
            )

        import app.service.orchestration.deck_generator

        app.service.orchestration.deck_generator.plan_deck = failing_plan_deck
        app.service.orchestration.deck_generator.write_content = AsyncMock(
            return_value=SlideContent(html_content="<html>Recovery content</html>")
        )

        # First attempt should fail
        with pytest.raises(Exception, match="Simulated planning failure"):
            await generate_deck(
                prompt="Test error recovery", llm=mock_llm, repo=mock_repo
            )

        # Verify failure was recorded
        mock_repo.update_deck_status.assert_called()

        # Reset for second attempt
        mock_repo.reset_mock()

        # Second attempt should succeed
        result = await generate_deck(
            prompt="Test error recovery - attempt 2", llm=mock_llm, repo=mock_repo
        )

        assert result is not None
        # Should have successful save calls
        assert len(mock_repo.save_deck.call_args_list) >= 2
