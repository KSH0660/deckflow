"""
Modular CSS Builder for Dynamic Slide Styling

This module builds custom CSS by combining:
1. Base Bootstrap framework
2. User preferences (layout/color/persona)
3. Layout-specific components based on slide type
"""

from pathlib import Path
from typing import Dict, List

from app.logging import get_logger

logger = get_logger(__name__)

# CSS file paths
CSS_DIR = Path(__file__).parent.parent.parent / "assets" / "css"
COMPONENTS_DIR = CSS_DIR / "components"

# Layout type to CSS component mapping
LAYOUT_COMPONENTS: Dict[str, str] = {
    "title_slide": "title_slide.css",
    "content_slide": "content_slide.css", 
    "comparison": "comparison.css",
    "data_visual": "content_slide.css",  # Reuse content_slide for data visuals
    "process_flow": "content_slide.css",  # Reuse content_slide for process flows
    "feature_showcase": "feature_showcase.css",
    "testimonial": "content_slide.css",  # Reuse content_slide for testimonials
    "call_to_action": "call_to_action.css",
}

# Color scheme CSS variables
COLOR_SCHEMES: Dict[str, Dict[str, str]] = {
    "professional_blue": {
        "--color-primary": "#1e40af",
        "--color-primary-rgb": "30, 64, 175",
        "--color-secondary": "#64748b", 
        "--color-secondary-rgb": "100, 116, 139",
        "--color-accent": "#0ea5e9",
        "--color-accent-rgb": "14, 165, 233",
        "--text-primary": "#1e293b",
        "--text-secondary": "#64748b",
    },
    "warm_corporate": {
        "--color-primary": "#dc2626",
        "--color-primary-rgb": "220, 38, 38", 
        "--color-secondary": "#d97706",
        "--color-secondary-rgb": "217, 119, 6",
        "--color-accent": "#ea580c",
        "--color-accent-rgb": "234, 88, 12",
        "--text-primary": "#1f2937",
        "--text-secondary": "#6b7280",
    },
    "modern_green": {
        "--color-primary": "#059669",
        "--color-primary-rgb": "5, 150, 105",
        "--color-secondary": "#6b7280", 
        "--color-secondary-rgb": "107, 114, 128",
        "--color-accent": "#34d399",
        "--color-accent-rgb": "52, 211, 153", 
        "--text-primary": "#111827",
        "--text-secondary": "#6b7280",
    }
}

# Persona spacing adjustments
PERSONA_STYLES: Dict[str, Dict[str, str]] = {
    "compact": {
        "padding": "2rem",
        "font-size-base": "1rem",
        "line-height": "1.5",
        "margin-bottom": "0.75rem",
    },
    "balanced": {
        "padding": "3rem", 
        "font-size-base": "1.125rem",
        "line-height": "1.6",
        "margin-bottom": "1rem",
    },
    "spacious": {
        "padding": "4rem",
        "font-size-base": "1.25rem", 
        "line-height": "1.7",
        "margin-bottom": "1.5rem",
    }
}


def _load_css_component(component_name: str) -> str:
    """Load CSS component file content"""
    component_path = COMPONENTS_DIR / component_name
    try:
        if component_path.exists():
            return component_path.read_text(encoding='utf-8')
        else:
            logger.warning(f"CSS component not found: {component_path}")
            return ""
    except Exception as e:
        logger.error(f"Error loading CSS component {component_name}: {e}")
        return ""


def _build_color_variables(color_preference: str) -> str:
    """Build CSS variables for color scheme"""
    if color_preference not in COLOR_SCHEMES:
        logger.warning(f"Unknown color scheme: {color_preference}, using professional_blue")
        color_preference = "professional_blue"
        
    variables = COLOR_SCHEMES[color_preference]
    css_vars = [f"    {key}: {value};" for key, value in variables.items()]
    
    return f"""
:root {{
{chr(10).join(css_vars)}
}}
"""


def _build_persona_styles(persona_preference: str, layout_preference: str) -> str:
    """Build persona-specific spacing and typography"""
    if persona_preference not in PERSONA_STYLES:
        logger.warning(f"Unknown persona: {persona_preference}, using balanced")
        persona_preference = "balanced"
        
    styles = PERSONA_STYLES[persona_preference]
    
    return f"""
/* {persona_preference.title()} Persona Styles */
.{layout_preference} {{
    padding: {styles['padding']};
}}

.{persona_preference}-text {{
    font-size: {styles['font-size-base']};
    line-height: {styles['line-height']};
}}

.{persona_preference}-spacing > * {{
    margin-bottom: {styles['margin-bottom']};
}}
"""


def build_slide_css(
    layout_type: str,
    layout_preference: str = "professional", 
    color_preference: str = "professional_blue",
    persona_preference: str = "balanced"
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
    logger.info(f"Building CSS for layout_type: {layout_type}, preferences: {layout_preference}/{color_preference}/{persona_preference}")
    
    css_parts = []
    
    # 1. Color variables
    css_parts.append(_build_color_variables(color_preference))
    
    # 2. Base slide container styles  
    css_parts.append("""
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
""")

    # 3. Layout-specific component CSS
    if layout_type in LAYOUT_COMPONENTS:
        component_css = _load_css_component(LAYOUT_COMPONENTS[layout_type])
        if component_css:
            css_parts.append(f"\n/* {layout_type.title()} Component */\n{component_css}")
    
    # 4. Persona spacing/typography 
    css_parts.append(_build_persona_styles(persona_preference, layout_preference))
    
    # 5. Layout preference modifier class
    css_parts.append(f"""
/* Layout Preference: {layout_preference} */
.slide-container {{
    /* Add layout-specific modifications here if needed */
}}
""")
    
    complete_css = "\n".join(css_parts)
    
    logger.debug(f"Generated CSS length: {len(complete_css)} characters")
    return complete_css


def get_available_components() -> List[str]:
    """Get list of available CSS components for documentation"""
    return list(LAYOUT_COMPONENTS.keys())


def get_available_color_schemes() -> List[str]:
    """Get list of available color schemes"""
    return list(COLOR_SCHEMES.keys())


def get_available_personas() -> List[str]:
    """Get list of available personas"""
    return list(PERSONA_STYLES.keys())