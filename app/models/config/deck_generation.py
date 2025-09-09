"""
Configuration models for deck generation.

This module contains configuration classes that define how decks should be generated.
These are separate from database models - they represent generation preferences and parameters.
"""

from pydantic import BaseModel, Field

from app.services.deck_planning.prompts import AVAILABLE_PROMPTS


class DeckGenerationConfig(BaseModel):
    """Configuration for deck generation process"""

    # Content generation settings
    persona: str = Field(
        default="EXPERT_DATA_STRATEGIST",
        description="Persona to use for content generation",
    )

    # Visual preferences (may influence color_theme in final deck)
    style_preferences: dict[str, str] = Field(
        default_factory=dict, description="Additional style preferences"
    )

    # Generation constraints
    max_slides: int = Field(
        default=10, ge=3, le=15, description="Maximum number of slides to generate"
    )

    min_slides: int = Field(
        default=3, ge=1, le=10, description="Minimum number of slides to generate"
    )

    # Content preferences
    include_data_points: bool = Field(
        default=True, description="Whether to include data points in slides"
    )

    include_expert_insights: bool = Field(
        default=True, description="Whether to include expert insights"
    )

    # Future extensibility
    generation_mode: str = Field(
        default="standard", description="Generation mode (standard, fast, detailed)"
    )

    def validate_persona(self) -> None:
        """Validate that the persona exists in available prompts"""
        if self.persona not in AVAILABLE_PROMPTS:
            raise ValueError(
                f"Invalid persona: {self.persona}. Available: {list(AVAILABLE_PROMPTS.keys())}"
            )

    @classmethod
    def from_request_style(
        cls, style: dict[str, str] | None = None
    ) -> "DeckGenerationConfig":
        """Create config from CreateDeckRequest.style field"""
        if not style:
            return cls()

        config_data = {}

        # Extract persona from style
        if "persona" in style:
            config_data["persona"] = style["persona"]

        # Extract other known config options
        if "max_slides" in style:
            try:
                config_data["max_slides"] = int(style["max_slides"])
            except ValueError:
                pass  # Use default if invalid

        if "generation_mode" in style:
            config_data["generation_mode"] = style["generation_mode"]

        # Store remaining style preferences
        remaining_style = {
            k: v
            for k, v in style.items()
            if k not in {"persona", "max_slides", "generation_mode"}
        }
        if remaining_style:
            config_data["style_preferences"] = remaining_style

        config = cls(**config_data)
        config.validate_persona()
        return config
