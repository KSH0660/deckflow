"""
Request models for deck API endpoints.

These models define the structure of incoming API requests.
They include validation, constraints, and transformation logic for user input.
"""
from typing import Optional, List, Dict
from pydantic import BaseModel, Field, validator

from app.service.file_processing import FileInfo


class CreateDeckRequest(BaseModel):
    """Request model for creating a new deck"""
    prompt: str = Field(..., min_length=5, max_length=5000, description="Deck generation prompt")
    style: Optional[Dict[str, str]] = Field(None, description="Optional styling preferences")
    files: Optional[List[FileInfo]] = Field(None, description="Optional uploaded files")

    @validator('prompt')
    def validate_prompt(cls, v):
        """Ensure prompt is not just whitespace"""
        if not v.strip():
            raise ValueError('Prompt cannot be empty or just whitespace')
        return v.strip()


class ModifySlideRequest(BaseModel):
    """Request model for modifying a slide"""
    modification_prompt: str = Field(
        ..., 
        min_length=5, 
        max_length=2000, 
        description="Instructions for slide modification"
    )

    @validator('modification_prompt')
    def validate_modification_prompt(cls, v):
        """Ensure modification prompt is not just whitespace"""
        if not v.strip():
            raise ValueError('Modification prompt cannot be empty or just whitespace')
        return v.strip()


class RevertSlideRequest(BaseModel):
    """Request model for reverting a slide to a specific version"""
    version_id: str = Field(..., description="ID of the version to revert to")

    @validator('version_id')
    def validate_version_id(cls, v):
        """Ensure version_id follows expected format"""
        if not v.strip():
            raise ValueError('Version ID cannot be empty')
        # Could add more specific format validation here
        return v.strip()


class SaveSlideContentRequest(BaseModel):
    """Request model for saving edited slide content"""
    html_content: str = Field(..., description="Updated HTML content of the slide")
    
    @validator('html_content')
    def validate_html_content(cls, v):
        """Basic HTML content validation"""
        if not v.strip():
            raise ValueError('HTML content cannot be empty')
        # Could add HTML validation here
        return v


class DeckExportRequest(BaseModel):
    """Request model for deck export parameters"""
    format: str = Field("html", pattern="^(html|pdf)$", description="Export format")
    layout: str = Field("widescreen", pattern="^(widescreen|a4|a4-landscape)$", description="Layout style")
    embed: str = Field("inline", pattern="^(inline|iframe)$", description="Embedding style")
    inline: bool = Field(False, description="Whether to display inline in browser")