"""
API endpoints for user preference options.

Exposes the unified enum system to the frontend.
"""

from fastapi import APIRouter

from app.models.enums import (
    get_layout_preferences,
    get_color_preferences, 
    get_persona_preferences,
    DEFAULT_LAYOUT_PREFERENCE,
    DEFAULT_COLOR_PREFERENCE,
    DEFAULT_PERSONA_PREFERENCE
)

router = APIRouter(tags=["preferences"])


@router.get("/preferences/layouts")
async def get_layout_preference_options():
    """Get all available layout preferences"""
    return {
        "options": get_layout_preferences(),
        "default": DEFAULT_LAYOUT_PREFERENCE.value
    }


@router.get("/preferences/colors") 
async def get_color_preference_options():
    """Get all available color preferences"""
    return {
        "options": get_color_preferences(),
        "default": DEFAULT_COLOR_PREFERENCE.value
    }


@router.get("/preferences/personas")
async def get_persona_preference_options():
    """Get all available persona preferences"""
    return {
        "options": get_persona_preferences(),
        "default": DEFAULT_PERSONA_PREFERENCE.value
    }


@router.get("/preferences")
async def get_all_preferences():
    """Get all preference options in one request"""
    return {
        "layouts": {
            "options": get_layout_preferences(),
            "default": DEFAULT_LAYOUT_PREFERENCE.value
        },
        "colors": {
            "options": get_color_preferences(),
            "default": DEFAULT_COLOR_PREFERENCE.value
        },
        "personas": {
            "options": get_persona_preferences(),
            "default": DEFAULT_PERSONA_PREFERENCE.value
        }
    }