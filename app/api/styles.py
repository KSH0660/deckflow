"""
Dynamic CSS Generation API for Slides
Generates optimized CSS based on layout/color/persona preferences
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.logging import get_logger
from app.models.enums import LayoutPreference, ColorPreference, PersonaPreference

router = APIRouter(tags=["styles"])
logger = get_logger(__name__)


def _load_css_file(file_path: str) -> str:
    """Load CSS content from file"""
    try:
        css_path = Path(__file__).parent.parent / "assets" / "css" / file_path
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        else:
            logger.warning(f"CSS file not found: {css_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading CSS file {file_path}: {e}")
        return ""


def _load_base_bootstrap() -> str:
    """Load base Bootstrap CSS"""
    try:
        css_path = (
            Path(__file__).parent.parent / "assets" / "bootstrap-styles.css"
        )
        if css_path.exists():
            return css_path.read_text(encoding="utf-8")
        else:
            logger.warning("Bootstrap styles not found")
            return ""
    except Exception as e:
        logger.error(f"Error loading Bootstrap CSS: {e}")
        return ""


@router.get("/styles/{layout}-{color}-{persona}.css")
async def get_dynamic_css(layout: str, color: str, persona: str):
    """
    Generate dynamic CSS based on preferences

    Example: /api/styles/professional-blue-balanced.css
    """
    try:
        # Load base Bootstrap CSS
        base_css = _load_base_bootstrap()

        # Load specific CSS files based on preferences
        layout_css = _load_css_file(f"layouts/{layout}.css")
        color_css = _load_css_file(f"colors/{color}.css")
        persona_css = _load_css_file(f"personas/{persona}.css")

        # Combine all CSS
        combined_css = f"""
/* Generated CSS for {layout}-{color}-{persona} */

/* Bootstrap CDN */
@import url('https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css');

/* Custom Bootstrap styles */
{base_css}

/* Layout-specific styles */
{layout_css}

/* Color scheme */
{color_css}

/* Persona spacing */
{persona_css}

/* Slide container base styles */
body {{
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, sans-serif;
}}

.slide-container {{
    width: 100vw;
    height: 100vh;
    aspect-ratio: 16/9;
}}
"""

        return Response(
            content=combined_css,
            media_type="text/css",
            headers={
                "Cache-Control": "public, max-age=3600",  # Cache for 1 hour
                "Content-Type": "text/css; charset=utf-8",
            },
        )

    except Exception as e:
        logger.error(f"Error generating CSS: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate CSS") from e


@router.get("/styles/slides.css")
async def get_combined_css():
    """
    Fallback: Get all styles combined (for compatibility)
    This includes all layout/color/persona combinations
    """
    try:
        base_css = _load_base_bootstrap()

        # Load all CSS files
        all_css_parts = [base_css]

        # Load all layouts
        for layout in LayoutPreference:
            layout_css = _load_css_file(f"layouts/{layout.value}.css")
            all_css_parts.append(f"/* {layout.value} layout */\n{layout_css}")

        # Load all colors
        for color in ColorPreference:
            color_css = _load_css_file(f"colors/{color.value}.css")
            all_css_parts.append(f"/* {color.value} colors */\n{color_css}")

        # Load all personas
        for persona in PersonaPreference:
            persona_css = _load_css_file(f"personas/{persona.value}.css")
            all_css_parts.append(f"/* {persona.value} persona */\n{persona_css}")

        # Add base slide styles
        all_css_parts.append(
            """
/* Slide container base styles */
body {
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, sans-serif;
}

.slide-container {
    width: 100vw;
    height: 100vh;
    aspect-ratio: 16/9;
}
"""
        )

        combined_css = "\n\n".join(all_css_parts)

        return Response(
            content=combined_css,
            media_type="text/css",
            headers={
                "Cache-Control": "public, max-age=3600",
                "Content-Type": "text/css; charset=utf-8",
            },
        )

    except Exception as e:
        logger.error(f"Error generating combined CSS: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate CSS") from e
