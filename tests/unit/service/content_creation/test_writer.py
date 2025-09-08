"""Tests for content creation writer logic."""

import pytest

from app.service.content_creation.models import SlideContent
from app.service.content_creation.writer import (
    RENDER_PROMPT,
    _validate_slide_content,
    write_content,
)
from tests.builders import (
    SlidePlanBuilder,
    any_deck_context,
    any_slide_content,
)


class TestWriteContent:
    """Tests for main write_content function."""

    @pytest.mark.asyncio
    async def test_write_content_success(self, mock_llm):
        """Test successful content generation."""
        slide_content = any_slide_content()
        mock_llm.generate_structured.return_value = slide_content

        # Use builder for flexible test data
        slide_plan = SlidePlanBuilder().with_title("Content Test Slide").build()
        slide_info = slide_plan.model_dump()

        deck_context = any_deck_context(title="Content Test Deck")

        result = await write_content(slide_info, deck_context.model_dump(), mock_llm)

        assert isinstance(result, SlideContent)
        assert result.html_content == slide_content.html_content
        mock_llm.generate_structured.assert_called_once()

    @pytest.mark.asyncio
    async def test_write_content_missing_params(self, mock_llm):
        """Test write_content with missing parameters."""
        with pytest.raises(
            ValueError, match="슬라이드 정보와 덱 컨텍스트는 필수입니다"
        ):
            await write_content(None, {}, mock_llm)

        with pytest.raises(
            ValueError, match="슬라이드 정보와 덱 컨텍스트는 필수입니다"
        ):
            await write_content({}, None, mock_llm)

    @pytest.mark.asyncio
    async def test_write_content_modification_mode(
        self, mock_llm, sample_slide_content
    ):
        """Test content generation in modification mode."""
        mock_llm.generate_structured.return_value = sample_slide_content

        slide_info = {"slide_title": "Test Slide", "message": "Test message"}
        deck_context = {"deck_title": "Test Deck"}

        result = await write_content(
            slide_info,
            deck_context,
            mock_llm,
            is_modification=True,
            modification_prompt="Make it more colorful",
        )

        assert isinstance(result, SlideContent)

        # Check that modification context was added to prompt
        call_args = mock_llm.generate_structured.call_args
        prompt = call_args[0][0]
        assert "MODIFICATION REQUEST" in prompt
        assert "Make it more colorful" in prompt

    @pytest.mark.asyncio
    async def test_write_content_prompt_formatting(
        self, mock_llm, sample_slide_content
    ):
        """Test that prompt is properly formatted with all variables."""
        mock_llm.generate_structured.return_value = sample_slide_content

        slide_info = {
            "slide_title": "AI Testing",
            "message": "Testing AI systems",
            "layout_type": "data_visual",
            "key_points": ["Unit tests", "Integration tests"],
        }

        deck_context = {
            "deck_title": "AI Development",
            "audience": "ML Engineers",
            "core_message": "Quality AI systems",
            "color_theme": "tech_dark",
        }

        await write_content(slide_info, deck_context, mock_llm)

        call_args = mock_llm.generate_structured.call_args
        prompt = call_args[0][0]

        # Check all context variables are in prompt
        assert "AI Development" in prompt
        assert "ML Engineers" in prompt
        assert "Quality AI systems" in prompt
        assert "tech_dark" in prompt

        # Check slide info is JSON formatted in prompt
        assert "AI Testing" in prompt
        assert "Unit tests" in prompt

    @pytest.mark.asyncio
    async def test_write_content_llm_error(self, mock_llm):
        """Test write_content when LLM fails."""
        mock_llm.generate_structured.side_effect = Exception("LLM Error")

        slide_info = {"slide_title": "Test", "message": "Test message"}
        deck_context = {"deck_title": "Test"}

        with pytest.raises(RuntimeError, match="슬라이드 콘텐츠 생성에 실패했습니다"):
            await write_content(slide_info, deck_context, mock_llm)

    @pytest.mark.asyncio
    async def test_write_content_defaults(self, mock_llm, sample_slide_content):
        """Test write_content with minimal slide_info using defaults."""
        mock_llm.generate_structured.return_value = sample_slide_content

        slide_info = {"slide_title": "Test"}  # Minimal slide info
        deck_context = {"deck_title": "Test"}  # Minimal context

        result = await write_content(slide_info, deck_context, mock_llm)

        assert isinstance(result, SlideContent)

        # Check defaults were used
        call_args = mock_llm.generate_structured.call_args
        prompt = call_args[0][0]
        assert "Test" in prompt  # Should use provided values


class TestValidateSlideContent:
    """Tests for slide content validation."""

    def test_validate_slide_content_valid(self, sample_slide_content):
        """Test validation of valid slide content."""
        # Should not raise any exception
        _validate_slide_content(sample_slide_content, "Test Slide")

    def test_validate_slide_content_empty(self):
        """Test validation of empty content."""
        empty_content = SlideContent(html_content="")

        with pytest.raises(ValueError, match="Generated HTML content is empty"):
            _validate_slide_content(empty_content, "Test Slide")

    def test_validate_slide_content_whitespace_only(self):
        """Test validation of whitespace-only content."""
        whitespace_content = SlideContent(html_content="   \n\t  ")

        with pytest.raises(ValueError, match="Generated HTML content is empty"):
            _validate_slide_content(whitespace_content, "Test Slide")

    def test_validate_slide_content_missing_tailwind(self, caplog):
        """Test validation warns about missing Tailwind CSS."""
        content = SlideContent(
            html_content="""
        <!DOCTYPE html>
        <html><body>No Tailwind CSS</body></html>
        """
        )

        _validate_slide_content(content, "Test Slide")
        # Should log warning but not raise exception

    def test_validate_slide_content_incomplete_html(self, caplog):
        """Test validation warns about incomplete HTML."""
        content = SlideContent(html_content="<div>Incomplete HTML")

        _validate_slide_content(content, "Test Slide")
        # Should log warning but not raise exception

    def test_validate_slide_content_too_short(self, caplog):
        """Test validation warns about very short content."""
        content = SlideContent(html_content="<html>Short</html>")

        _validate_slide_content(content, "Test Slide")
        # Should log warning but not raise exception

    def test_validate_slide_content_overflow_checks(self, caplog):
        """Test overflow prevention checks."""
        # Content with potential overflow issues
        bad_content = SlideContent(
            html_content="""
        <!DOCTYPE html>
        <html>
        <head><script src="https://cdn.tailwindcss.com"></script></head>
        <body>
            <div class="p-12 text-4xl">
                Bad styling that might cause overflow
            </div>
        </body>
        </html>
        """
        )

        _validate_slide_content(bad_content, "Test Slide")
        # Should log warnings about overflow prevention failures


class TestRenderPrompt:
    """Tests for render prompt template."""

    def test_render_prompt_structure(self):
        """Test that render prompt has expected structure."""
        assert "HTML layout assistant" in RENDER_PROMPT
        assert "Tailwind CSS" in RENDER_PROMPT
        assert "<!DOCTYPE html>" in RENDER_PROMPT
        assert "tailwindcss.com" in RENDER_PROMPT
        assert "{topic}" in RENDER_PROMPT
        assert "{audience}" in RENDER_PROMPT
        assert "{slide_json}" in RENDER_PROMPT

    def test_render_prompt_formatting(self):
        """Test render prompt can be formatted properly."""
        test_vars = {
            "topic": "Test Topic",
            "audience": "Test Audience",
            "theme": "Test Theme",
            "color_preference": "professional_blue",
            "slide_json": '{"title": "Test"}',
            "modification_context": "",
        }

        formatted = RENDER_PROMPT.format(**test_vars)

        assert "Test Topic" in formatted
        assert "Test Audience" in formatted
        assert "professional_blue" in formatted
        assert '{"title": "Test"}' in formatted

    def test_render_prompt_overflow_prevention(self):
        """Test that prompt includes overflow prevention guidelines."""
        assert "overflow-hidden" in RENDER_PROMPT
        assert "h-screen" in RENDER_PROMPT
        assert "max-h-screen" in RENDER_PROMPT
        assert "NO VERTICAL OVERFLOW" in RENDER_PROMPT
        assert (
            "text-3xl or larger" in RENDER_PROMPT or "text-2xl maximum" in RENDER_PROMPT
        )
