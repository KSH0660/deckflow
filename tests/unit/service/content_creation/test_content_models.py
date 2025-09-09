"""Tests for content creation models."""

from app.services.content_creation.models import (
    COLOR_THEME_MAPPING,
    LAYOUT_TYPE_ASSET_MAPPING,
    SlideContent,
)


class TestSlideContent:
    """Tests for SlideContent model."""

    def test_valid_slide_content_creation(self, sample_slide_content):
        """Test creating valid slide content."""
        assert sample_slide_content.html_content is not None
        assert len(sample_slide_content.html_content) > 0
        assert "<!DOCTYPE html>" in sample_slide_content.html_content

    def test_slide_content_empty_html(self):
        """Test slide content with empty HTML."""
        # Empty string should be valid (validation happens in writer)
        content = SlideContent(html_content="")
        assert content.html_content == ""

    def test_slide_content_html_structure(self, sample_slide_content):
        """Test that sample HTML has expected structure."""
        html = sample_slide_content.html_content
        assert "<html>" in html
        assert "</html>" in html
        assert "tailwindcss.com" in html
        # Builder default heading is 'Test Slide'
        assert "Test Slide" in html
        assert "h-screen" in html or "max-h-screen" in html

    def test_slide_content_serialization(self, sample_slide_content):
        """Test model serialization."""
        data = sample_slide_content.model_dump()
        assert "html_content" in data
        assert data["html_content"] == sample_slide_content.html_content

        # Test deserialization
        new_content = SlideContent(**data)
        assert new_content.html_content == sample_slide_content.html_content


class TestColorThemeMapping:
    """Tests for color theme configuration."""

    def test_color_theme_mapping_structure(self):
        """Test that all color themes have required color keys."""
        required_keys = {
            "primary",
            "secondary",
            "accent",
            "background",
            "surface",
            "text_primary",
            "text_secondary",
        }

        for theme_name, colors in COLOR_THEME_MAPPING.items():
            assert isinstance(theme_name, str)
            assert isinstance(colors, dict)
            assert set(colors.keys()) == required_keys

            # Check all colors are valid hex codes
            for _color_key, color_value in colors.items():
                assert isinstance(color_value, str)
                assert color_value.startswith("#")
                assert len(color_value) == 7  # #RRGGBB format

    def test_specific_color_themes(self):
        """Test specific color theme values."""
        # Test professional blue theme
        blue_theme = COLOR_THEME_MAPPING["professional_blue"]
        assert blue_theme["primary"] == "#1e40af"
        assert blue_theme["background"] == "#ffffff"
        assert blue_theme["text_primary"] == "#1e293b"

        # Test tech dark theme
        dark_theme = COLOR_THEME_MAPPING["tech_dark"]
        assert dark_theme["background"] == "#000000"
        assert dark_theme["text_primary"] == "#f9fafb"
        assert dark_theme["surface"] == "#1f2937"

    def test_color_theme_completeness(self):
        """Test that we have all expected color themes."""
        expected_themes = {
            "professional_blue",
            "corporate_gray",
            "vibrant_purple",
            "modern_teal",
            "energetic_orange",
            "nature_green",
            "elegant_burgundy",
            "tech_dark",
            "warm_sunset",
            "minimal_monochrome",
        }

        actual_themes = set(COLOR_THEME_MAPPING.keys())
        assert actual_themes == expected_themes

    def test_color_hex_format_validation(self):
        """Test that all color values follow proper hex format."""
        hex_pattern = r"^#[0-9a-fA-F]{6}$"
        import re

        for theme_name, colors in COLOR_THEME_MAPPING.items():
            for color_name, color_value in colors.items():
                assert re.match(
                    hex_pattern, color_value
                ), f"Invalid hex color {color_value} in {theme_name}.{color_name}"


class TestLayoutTypeAssetMapping:
    """Tests for layout type asset mapping."""

    def test_layout_asset_mapping_structure(self):
        """Test layout asset mapping has expected structure."""
        expected_layouts = {
            "title_slide",
            "content_slide",
            "comparison",
            "data_visual",
            "process_flow",
            "feature_showcase",
            "testimonial",
            "call_to_action",
        }

        actual_layouts = set(LAYOUT_TYPE_ASSET_MAPPING.keys())
        assert actual_layouts == expected_layouts

    def test_layout_asset_values(self):
        """Test that asset mapping values are reasonable."""
        for layout_type, asset_folder in LAYOUT_TYPE_ASSET_MAPPING.items():
            assert isinstance(layout_type, str)
            assert isinstance(asset_folder, str)
            assert len(asset_folder) > 0
            # Asset folder should match layout type (based on current implementation)
            assert asset_folder == layout_type

    def test_specific_layout_mappings(self):
        """Test specific layout mappings."""
        assert LAYOUT_TYPE_ASSET_MAPPING["title_slide"] == "title_slide"
        assert LAYOUT_TYPE_ASSET_MAPPING["data_visual"] == "data_visual"
        assert LAYOUT_TYPE_ASSET_MAPPING["call_to_action"] == "call_to_action"
