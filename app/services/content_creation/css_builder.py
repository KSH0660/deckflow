"""
Modular CSS Builder for Dynamic Slide Styling

This module builds custom CSS by combining:
1. Base Bootstrap framework
2. User preferences (layout/color/persona)
3. Layout-specific components based on slide type
"""

from pathlib import Path

from app.logging import get_logger
from app.models.enums import (
    ColorPreference,
    LayoutPreference,
    LayoutType,
    PersonaPreference,
    validate_color_preference,
    validate_layout_preference,
    validate_layout_type,
    validate_persona_preference,
)

logger = get_logger(__name__)

# CSS file paths
CSS_DIR = Path(__file__).parent.parent.parent / "assets" / "css"
COMPONENTS_DIR = CSS_DIR / "components"

# Layout type to CSS component mapping
LAYOUT_COMPONENTS: dict[LayoutType, str] = {
    LayoutType.TITLE_SLIDE: "title_slide.css",
    LayoutType.CONTENT_SLIDE: "content_slide.css",
    LayoutType.COMPARISON: "comparison.css",
    LayoutType.DATA_VISUAL: "data_visual.css",
    LayoutType.PROCESS_FLOW: "process_flow.css",
    LayoutType.FEATURE_SHOWCASE: "feature_showcase.css",
    LayoutType.TESTIMONIAL: "testimonial.css",
    LayoutType.CALL_TO_ACTION: "call_to_action.css",
    LayoutType.TWO_COLUMN: "two_column.css",
    LayoutType.STATS_SHOWCASE: "stats_showcase.css",
    LayoutType.TIMELINE: "timeline.css",
}

# Color scheme CSS variables
COLOR_SCHEMES: dict[ColorPreference, dict[str, str]] = {
    ColorPreference.PROFESSIONAL_BLUE: {
        "--color-primary": "#1e40af",
        "--color-primary-rgb": "30, 64, 175",
        "--color-secondary": "#64748b",
        "--color-secondary-rgb": "100, 116, 139",
        "--color-accent": "#0ea5e9",
        "--color-accent-rgb": "14, 165, 233",
        "--text-primary": "#1e293b",
        "--text-secondary": "#64748b",
    },
    ColorPreference.WARM_CORPORATE: {
        "--color-primary": "#dc2626",
        "--color-primary-rgb": "220, 38, 38",
        "--color-secondary": "#d97706",
        "--color-secondary-rgb": "217, 119, 6",
        "--color-accent": "#ea580c",
        "--color-accent-rgb": "234, 88, 12",
        "--text-primary": "#1f2937",
        "--text-secondary": "#6b7280",
    },
    ColorPreference.MODERN_GREEN: {
        "--color-primary": "#059669",
        "--color-primary-rgb": "5, 150, 105",
        "--color-secondary": "#6b7280",
        "--color-secondary-rgb": "107, 114, 128",
        "--color-accent": "#34d399",
        "--color-accent-rgb": "52, 211, 153",
        "--text-primary": "#111827",
        "--text-secondary": "#6b7280",
    },
}

# Persona spacing adjustments
PERSONA_STYLES: dict[PersonaPreference, dict[str, str]] = {
    PersonaPreference.COMPACT: {
        "padding": "2rem",
        "font-size-base": "1rem",
        "line-height": "1.5",
        "margin-bottom": "0.75rem",
    },
    PersonaPreference.BALANCED: {
        "padding": "3rem",
        "font-size-base": "1.125rem",
        "line-height": "1.6",
        "margin-bottom": "1rem",
    },
    PersonaPreference.SPACIOUS: {
        "padding": "4rem",
        "font-size-base": "1.25rem",
        "line-height": "1.7",
        "margin-bottom": "1.5rem",
    },
}


def _load_css_component(component_name: str) -> str:
    """Load CSS component file content"""
    component_path = COMPONENTS_DIR / component_name
    try:
        if component_path.exists():
            return component_path.read_text(encoding="utf-8")
        else:
            logger.warning(f"CSS component not found: {component_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading CSS component {component_name}: {e}")
        return ""


def _build_color_variables(color_preference: ColorPreference) -> str:
    """Build CSS variables for color scheme"""
    if color_preference not in COLOR_SCHEMES:
        logger.warning(
            f"Unknown color scheme: {color_preference}, using professional_blue"
        )
        color_preference = ColorPreference.PROFESSIONAL_BLUE

    variables = COLOR_SCHEMES[color_preference]
    css_vars = [f"    {key}: {value};" for key, value in variables.items()]

    return f"""
:root {{
{chr(10).join(css_vars)}
}}
"""


def _build_persona_styles(
    persona_preference: PersonaPreference, layout_preference: LayoutPreference
) -> str:
    """Build persona-specific spacing and typography"""
    if persona_preference not in PERSONA_STYLES:
        logger.warning(f"Unknown persona: {persona_preference}, using balanced")
        persona_preference = PersonaPreference.BALANCED

    styles = PERSONA_STYLES[persona_preference]

    return f"""
/* {persona_preference.value.title()} Persona Styles */
.{layout_preference.value} {{
    padding: {styles['padding']};
}}

.{persona_preference.value}-text {{
    font-size: {styles['font-size-base']};
    line-height: {styles['line-height']};
}}

.{persona_preference.value}-spacing > * {{
    margin-bottom: {styles['margin-bottom']};
}}
"""


def build_slide_css(
    layout_type: LayoutType | str,
    layout_preference: LayoutPreference | str = LayoutPreference.PROFESSIONAL,
    color_preference: ColorPreference | str = ColorPreference.PROFESSIONAL_BLUE,
    persona_preference: PersonaPreference | str = PersonaPreference.BALANCED,
) -> str:
    """
    Build complete CSS for a specific slide

    Args:
        layout_type: The slide layout type (title_slide, content_slide, etc.)
        layout_preference: User's layout preference (professional, creative, minimal)
        color_preference: User's color preference
        persona_preference: User's persona preference (spacing/typography)

    Returns:
        Complete CSS string ready to be injected into HTML head
    """
    # Validate and convert to enums
    if isinstance(layout_type, str):
        layout_type = validate_layout_type(layout_type)
    if isinstance(layout_preference, str):
        layout_preference = validate_layout_preference(layout_preference)
    if isinstance(color_preference, str):
        color_preference = validate_color_preference(color_preference)
    if isinstance(persona_preference, str):
        persona_preference = validate_persona_preference(persona_preference)

    logger.info(
        f"Building CSS for layout_type: {layout_type.value}, preferences: {layout_preference.value}/{color_preference.value}/{persona_preference.value}"
    )

    css_parts = []

    # 1. Color variables
    css_parts.append(_build_color_variables(color_preference))

    # 2. Base slide container styles
    css_parts.append(
        """
/* Base Slide Styles */
body {
    margin: 0;
    padding: 0;
    font-family: system-ui, -apple-system, sans-serif;
}

.slide-container {
    width: 100vw;
    height: 100vh;
    aspect-ratio: 16/9;
    max-width: 1200px;
    margin: 0 auto;
    background: white;
    box-shadow: 0 10px 30px rgba(0,0,0,0.1);
    overflow: hidden;
    position: relative;
}
"""
    )

    # 3. Layout-specific component CSS
    if layout_type in LAYOUT_COMPONENTS:
        component_css = _load_css_component(LAYOUT_COMPONENTS[layout_type])
        if component_css:
            css_parts.append(
                f"\n/* {layout_type.title()} Component */\n{component_css}"
            )

    # 4. Persona spacing/typography
    css_parts.append(_build_persona_styles(persona_preference, layout_preference))

    # 5. Layout preference modifier class
    css_parts.append(
        f"""
/* Layout Preference: {layout_preference.value} */
.slide-container {{
    /* Add layout-specific modifications here if needed */
}}
"""
    )

    complete_css = "\n".join(css_parts)

    logger.debug(f"Generated CSS length: {len(complete_css)} characters")
    return complete_css


def get_available_components() -> list[LayoutType]:
    """Get list of available CSS components for documentation"""
    return list(LAYOUT_COMPONENTS.keys())


def get_available_color_schemes() -> list[ColorPreference]:
    """Get list of available color schemes"""
    return list(COLOR_SCHEMES.keys())


def get_available_personas() -> list[PersonaPreference]:
    """Get list of available personas"""
    return list(PERSONA_STYLES.keys())
