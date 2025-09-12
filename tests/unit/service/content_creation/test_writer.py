"""Tests for content creation writer logic."""

import pytest

from app.services.content_creation.models import SlideContent
from app.services.content_creation.writer import (
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
        # Check that the result is a full HTML document
        assert result.html_content.startswith("<!DOCTYPE html>")
        assert "bootstrap.min.css" in result.html_content
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
        """Test that prompt is properly formatted with slide data."""
        mock_llm.generate_structured.return_value = sample_slide_content

        slide_info = {
            "slide_title": "AI Testing",
            "message": "Testing AI systems",
            "layout_type": "content_slide",
            "key_points": ["Unit tests", "Integration tests"],
        }

        deck_context = {
            "deck_title": "AI Development",
            "audience": "ML Engineers",
            "core_message": "Quality AI systems",
            "color_theme": "tech_dark",
            "layout_preference": "professional",
            "persona_preference": "balanced",
        }

        await write_content(slide_info, deck_context, mock_llm)

        call_args = mock_llm.generate_structured.call_args
        prompt = call_args[0][0]

        # Check that slide_data is in the prompt
        assert "SLIDE DATA: " in prompt
        assert "'slide_title': 'AI Testing'" in prompt
        assert "'key_points': ['Unit tests', 'Integration tests']" in prompt

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

    def test_validate_slide_content_valid(self):
        """Test validation of valid slide content."""
        from tests.builders import SlideContentBuilder
        valid_content = SlideContentBuilder().minimal().build()
        warnings = _validate_slide_content(valid_content, "Test Slide")
        assert not warnings

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

    def test_validate_slide_content_missing_bootstrap(self):
        """Test validation warns about missing bootstrap CSS."""
        content = SlideContent(
            html_content='<!DOCTYPE html><html><body>No bootstrap CSS</body></html>'
        )

        warnings = _validate_slide_content(content, "Test Slide")
        assert "Bootstrap CSS가 누락되었습니다." in warnings

    def test_validate_slide_content_incomplete_html(self):
        """Test validation warns about incomplete HTML."""
        content = SlideContent(html_content="<div>Incomplete HTML")

        warnings = _validate_slide_content(content, "Test Slide")
        assert any("완전한 HTML 문서가 아닙니다." in w for w in warnings)

    def test_validate_slide_content_too_short(self):
        """Test validation warns about very short content."""
        content = SlideContent(html_content="<html>Short</html>")

        warnings = _validate_slide_content(content, "Test Slide")
        assert any("생성된 HTML이 너무 짧습니다." in w for w in warnings)

    def test_validate_slide_content_overflow_checks(self):
        """Test overflow prevention checks."""
        # Content with potential overflow issues
        bad_content = SlideContent(
            html_content='''
        <!DOCTYPE html>
        <html>
        <head><link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"></head>
        <body>
            <ul>
                <li>Point 1</li>
                <li>Point 2</li>
                <li>Point 3</li>
                <li>Point 4</li>
                <li>Point 5</li>
                <li>Point 6</li>
                <li>Point 7</li>
            </ul>
        </body>
        </html>
        '''
        )

        warnings = _validate_slide_content(bad_content, "Test Slide")
        assert any("콘텐츠가 화면을 초과할 수 있습니다" in w for w in warnings)

