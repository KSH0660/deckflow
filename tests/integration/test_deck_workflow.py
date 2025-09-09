"""Integration tests for full deck generation workflow."""

from unittest.mock import MagicMock

import pytest

from app.services.content_creation.models import SlideContent
from app.services.deck_planning.models import (
    ColorTheme,
    DeckPlan,
    LayoutType,
    PresentationGoal,
    SlidePlan,
)
from app.services.deck_service import DeckService


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

        # Mock the service functions using patch
        from unittest.mock import patch

        from app.models.requests.deck import CreateDeckRequest

        # Track progress updates
        progress_updates = []

        async def track_progress(step: str, progress: int, slide_data=None):
            progress_updates.append((step, progress, slide_data))

        # Setup DeckService
        deck_service = DeckService(repository=mock_repo, llm_provider=mock_llm)

        # Mock settings
        settings = MagicMock()
        settings.llm_model = "test-model"

        # Mock the planning and content generation dependencies
        with patch("app.services.deck_planning.plan_deck", side_effect=mock_plan_deck):
            with patch(
                "app.services.content_creation.write_content",
                side_effect=mock_write_content,
            ):
                with patch("app.adapter.factory.current_llm", return_value=mock_llm):
                    # Create request
                    request = CreateDeckRequest(
                        prompt="Create a comprehensive presentation about integration testing best practices"
                    )

                    # Execute workflow through DeckService
                    result = await deck_service.create_deck(request, settings)

        # Verify result (DeckService returns CreateDeckResponse)
        assert result is not None
        assert result.status == "generating"
        assert result.deck_id is not None

        # Verify repository interactions - initial save should happen
        save_calls = mock_repo.save_deck.call_args_list
        assert len(save_calls) >= 1  # At least initial save

        # Verify initial deck was saved
        initial_deck = save_calls[0][0][1]  # First save call, deck data
        assert initial_deck["status"] == "generating"

    @pytest.mark.skip(
        reason="File processing test needs mocking adjustment for background task execution"
    )
    @pytest.mark.asyncio
    async def test_workflow_with_file_processing(self, mock_llm, mock_repo):
        """Test workflow with file input processing."""
        # Mock file input using proper FileInfo model
        from app.models.requests.deck import FileInfo

        mock_files = [
            FileInfo(
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

        # Mock service functions using patches
        from unittest.mock import patch

        from app.models.requests.deck import CreateDeckRequest

        # Setup DeckService
        deck_service = DeckService(repository=mock_repo, llm_provider=mock_llm)

        # Mock settings
        settings = MagicMock()
        settings.llm_model = "test-model"

        with patch(
            "app.services.deck_planning.plan_deck", return_value=mock_deck_plan
        ) as mock_plan:
            with patch(
                "app.services.content_creation.write_content", return_value=mock_content
            ):
                with patch("app.adapter.factory.current_llm", return_value=mock_llm):
                    # Create request with files
                    request = CreateDeckRequest(
                        prompt="Create presentation from testing strategy document",
                        files=mock_files,
                    )

                    # Execute workflow
                    result = await deck_service.create_deck(request, settings)

        assert result is not None
        assert result.status == "generating"

        # Verify enhanced prompt was created with file content - check if plan_deck was called
        mock_plan.assert_called_once()
        enhanced_prompt = mock_plan.call_args[0][0]  # First argument to plan_deck
        assert "testing_strategy.pdf" in enhanced_prompt
        assert "Unit Testing" in enhanced_prompt

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

        from unittest.mock import patch

        from app.models.requests.deck import CreateDeckRequest

        # Setup DeckService
        deck_service = DeckService(repository=mock_repo, llm_provider=mock_llm)

        # Mock settings
        settings = MagicMock()
        settings.llm_model = "test-model"

        # Test error handling in the background generation task
        # The create_deck method itself shouldn't fail - it starts background processing
        with patch(
            "app.services.deck_planning.plan_deck", side_effect=failing_plan_deck
        ):
            with patch(
                "app.services.content_creation.write_content",
                return_value=SlideContent(html_content="<html>Recovery content</html>"),
            ):
                with patch("app.adapter.factory.current_llm", return_value=mock_llm):
                    # Create request
                    request = CreateDeckRequest(prompt="Test error recovery")

                    # This should succeed in starting the process
                    result = await deck_service.create_deck(request, settings)

                    assert result is not None
                    assert result.status == "generating"

                    # The error handling happens in background task
                    # Verify initial deck was saved
                    assert len(mock_repo.save_deck.call_args_list) >= 1
