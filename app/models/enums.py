"""
Unified Enum System for DeckFlow

This module defines all enums used throughout the system to ensure
consistency between frontend, backend, and assets.
"""

from enum import Enum


# Layout Types (determined by AI planning)
class LayoutType(str, Enum):
    """Slide layout types determined by deck planning AI"""
    TITLE_SLIDE = "title_slide"
    CONTENT_SLIDE = "content_slide" 
    COMPARISON = "comparison"
    DATA_VISUAL = "data_visual"
    PROCESS_FLOW = "process_flow"
    FEATURE_SHOWCASE = "feature_showcase"
    TESTIMONIAL = "testimonial"
    CALL_TO_ACTION = "call_to_action"


# Layout Preferences (user choice)
class LayoutPreference(str, Enum):
    """User's preferred layout style"""
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    MINIMAL = "minimal"


# Color Preferences (user choice) 
class ColorPreference(str, Enum):
    """User's preferred color scheme"""
    PROFESSIONAL_BLUE = "professional_blue"
    WARM_CORPORATE = "warm_corporate"
    MODERN_GREEN = "modern_green"


# Persona Preferences (user choice - spacing/typography)
class PersonaPreference(str, Enum):
    """User's preferred spacing and typography density"""
    COMPACT = "compact"
    BALANCED = "balanced" 
    SPACIOUS = "spacious"


# Presentation Goals (for planning)
class PresentationGoal(str, Enum):
    """Overall presentation objective"""
    PERSUADE = "persuade"
    INFORM = "inform"
    INSPIRE = "inspire"
    EDUCATE = "educate"


# Configuration mappings for each preference type
LAYOUT_PREFERENCE_CONFIG = {
    LayoutPreference.PROFESSIONAL: {
        "name": "프로페셔널",
        "description": "기업용 구조화된 레이아웃", 
        "icon": "💼"
    },
    LayoutPreference.CREATIVE: {
        "name": "크리에이티브",
        "description": "역동적이고 현대적인 레이아웃",
        "icon": "🎨"
    },
    LayoutPreference.MINIMAL: {
        "name": "미니멀", 
        "description": "깔끔하고 간단한 레이아웃",
        "icon": "📝"
    }
}

COLOR_PREFERENCE_CONFIG = {
    ColorPreference.PROFESSIONAL_BLUE: {
        "name": "프로페셔널 블루",
        "description": "신뢰감 있는 파란색 조합",
        "preview": "#1e40af"
    },
    ColorPreference.WARM_CORPORATE: {
        "name": "웜 코퍼릿",
        "description": "따뜻한 기업 색상 조합", 
        "preview": "#dc2626"
    },
    ColorPreference.MODERN_GREEN: {
        "name": "모던 그린",
        "description": "현대적인 녹색 조합",
        "preview": "#059669"
    }
}

PERSONA_PREFERENCE_CONFIG = {
    PersonaPreference.COMPACT: {
        "name": "컴팩트",
        "description": "밀도 높은 정보 전달",
        "icon": "📋"
    },
    PersonaPreference.BALANCED: {
        "name": "밸런스드", 
        "description": "균형잡힌 일반적 사용",
        "icon": "⚖️"
    },
    PersonaPreference.SPACIOUS: {
        "name": "스페이셔스",
        "description": "여유로운 편안한 읽기",
        "icon": "🌅"
    }
}

# Default values
DEFAULT_LAYOUT_PREFERENCE = LayoutPreference.PROFESSIONAL
DEFAULT_COLOR_PREFERENCE = ColorPreference.PROFESSIONAL_BLUE  
DEFAULT_PERSONA_PREFERENCE = PersonaPreference.BALANCED


# Validation functions
def validate_layout_preference(value: str) -> LayoutPreference:
    """Validate and convert string to LayoutPreference enum"""
    try:
        return LayoutPreference(value)
    except ValueError:
        return DEFAULT_LAYOUT_PREFERENCE


def validate_color_preference(value: str) -> ColorPreference:
    """Validate and convert string to ColorPreference enum"""
    try:
        return ColorPreference(value)
    except ValueError:
        return DEFAULT_COLOR_PREFERENCE


def validate_persona_preference(value: str) -> PersonaPreference:
    """Validate and convert string to PersonaPreference enum"""
    try:
        return PersonaPreference(value)
    except ValueError:
        return DEFAULT_PERSONA_PREFERENCE


def validate_layout_type(value: str) -> LayoutType:
    """Validate and convert string to LayoutType enum"""
    try:
        return LayoutType(value)
    except ValueError:
        return LayoutType.CONTENT_SLIDE  # Safe default


# Export functions for frontend compatibility
def get_layout_preferences():
    """Get all layout preferences for frontend"""
    return [
        {
            "id": pref.value,
            "name": config["name"],
            "description": config["description"],
            "icon": config["icon"]
        }
        for pref, config in LAYOUT_PREFERENCE_CONFIG.items()
    ]


def get_color_preferences():
    """Get all color preferences for frontend"""
    return [
        {
            "id": pref.value,
            "name": config["name"], 
            "description": config["description"],
            "preview": config["preview"]
        }
        for pref, config in COLOR_PREFERENCE_CONFIG.items()
    ]


def get_persona_preferences():
    """Get all persona preferences for frontend"""
    return [
        {
            "id": pref.value,
            "name": config["name"],
            "description": config["description"], 
            "icon": config["icon"]
        }
        for pref, config in PERSONA_PREFERENCE_CONFIG.items()
    ]