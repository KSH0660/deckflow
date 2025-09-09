"""
Response models for deck API endpoints.

These models define the structure of outgoing API responses.
They should be optimized for client consumption and may differ from database models.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field

from app.models.database.deck import DeckDB, SlideDB


class CreateDeckResponse(BaseModel):
    """Response model for deck creation"""
    deck_id: str = Field(..., description="Unique identifier of the created deck")
    status: str = Field(default="generating", description="Current status of the deck")


class DeckStatusResponse(BaseModel):
    """Response model for deck status information"""
    deck_id: str = Field(..., description="Unique identifier of the deck")
    status: str = Field(..., description="Current status of the deck")
    slide_count: int = Field(..., description="Number of slides in the deck")
    progress: Optional[int] = Field(None, description="Progress percentage (0-100)")
    step: Optional[str] = Field(None, description="Current processing step")
    created_at: datetime = Field(..., description="When the deck was created")
    updated_at: Optional[datetime] = Field(None, description="When the deck was last updated")
    completed_at: Optional[datetime] = Field(None, description="When the deck was completed")

    @classmethod
    def from_db_model(cls, deck: DeckDB) -> "DeckStatusResponse":
        """Create response from database model"""
        return cls(
            deck_id=str(deck.id),
            status=deck.status,
            slide_count=len(deck.slides),
            progress=deck.progress,
            step=deck.step,
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            completed_at=deck.completed_at
        )


class DeckListItemResponse(BaseModel):
    """Response model for deck list items"""
    deck_id: str = Field(..., description="Unique identifier of the deck")
    title: str = Field(..., description="Title of the deck")
    status: str = Field(..., description="Current status of the deck")
    slide_count: int = Field(..., description="Number of slides in the deck")
    created_at: datetime = Field(..., description="When the deck was created")
    updated_at: Optional[datetime] = Field(None, description="When the deck was last updated")
    completed_at: Optional[datetime] = Field(None, description="When the deck was completed")

    @classmethod
    def from_db_model(cls, deck: DeckDB) -> "DeckListItemResponse":
        """Create response from database model"""
        return cls(
            deck_id=str(deck.id),
            title=deck.deck_title,
            status=deck.status,
            slide_count=len(deck.slides),
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            completed_at=deck.completed_at
        )


class ModifySlideResponse(BaseModel):
    """Response model for slide modification"""
    deck_id: str = Field(..., description="Unique identifier of the deck")
    slide_order: int = Field(..., description="Order of the modified slide")
    status: str = Field(default="modifying", description="Current status of the modification")


class SlideVersionResponse(BaseModel):
    """Response model for a single slide version"""
    version_id: str = Field(..., description="Unique identifier of the version")
    content: str = Field(..., description="HTML content of this version")
    timestamp: datetime = Field(..., description="When this version was created")
    is_current: bool = Field(..., description="Whether this is the current version")
    created_by: str = Field(..., description="Who created this version (user/system)")


class SlideVersionHistoryResponse(BaseModel):
    """Response model for slide version history"""
    deck_id: str = Field(..., description="Unique identifier of the deck")
    slide_order: int = Field(..., description="Order of the slide")
    versions: List[SlideVersionResponse] = Field(..., description="List of all versions")
    current_version_id: str = Field(..., description="ID of the current version")

    @classmethod
    def from_db_slide(cls, deck_id: str, slide_order: int, slide: SlideDB) -> "SlideVersionHistoryResponse":
        """Create response from database slide model"""
        versions = [
            SlideVersionResponse(
                version_id=version.version_id,
                content=version.content,
                timestamp=version.timestamp,
                is_current=version.is_current,
                created_by=version.created_by
            )
            for version in (slide.versions or [])
        ]
        
        current_version_id = slide.content.current_version_id or ""
        
        return cls(
            deck_id=deck_id,
            slide_order=slide_order,
            versions=versions,
            current_version_id=current_version_id
        )


class RevertSlideResponse(BaseModel):
    """Response model for slide version revert"""
    deck_id: str = Field(..., description="Unique identifier of the deck")
    slide_order: int = Field(..., description="Order of the reverted slide")
    reverted_to_version: str = Field(..., description="ID of the version reverted to")
    status: str = Field(default="success", description="Status of the revert operation")


class SaveSlideContentResponse(BaseModel):
    """Response model for saving slide content"""
    status: str = Field(default="success", description="Status of the save operation")
    message: str = Field(..., description="Human-readable message")
    version_id: Optional[str] = Field(None, description="ID of the new version created")
    version_count: int = Field(..., description="Total number of versions for this slide")


class FileUploadResponse(BaseModel):
    """Response model for file upload"""
    filename: str = Field(..., description="Name of the uploaded file")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of the file in bytes")
    extracted_text: str = Field(..., description="Extracted text content")
    message: str = Field(default="파일이 성공적으로 처리되었습니다.", description="Success message")


# For backward compatibility, re-export the old names
SlideVersion = SlideVersionResponse
SlideVersionHistory = SlideVersionHistoryResponse