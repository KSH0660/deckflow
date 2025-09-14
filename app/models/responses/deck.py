"""
Response models for deck API endpoints.

These models define the structure of outgoing API responses.
They should be optimized for client consumption and may differ from database models.
"""

from datetime import datetime

from pydantic import BaseModel, Field

from app.models.database.deck import DeckDB, SlideDB
from app.models.enums import DeckStatus


class DeckResponse(BaseModel):
    """Unified response model for deck operations"""

    deck_id: str = Field(..., description="Unique identifier of the deck")
    status: DeckStatus = Field(..., description="Current status of the deck")
    slide_count: int = Field(..., description="Number of slides in the deck")
    created_at: datetime = Field(..., description="When the deck was created")
    updated_at: datetime | None = Field(
        None, description="When the deck was last updated"
    )
    completed_at: datetime | None = Field(
        None, description="When the deck was completed"
    )

    # Optional fields for detailed views
    title: str | None = Field(None, description="Title of the deck (for list views)")
    progress: int | None = Field(None, description="Progress percentage (0-100)")
    status_message: str | None = Field(
        None, description="Human-readable status message"
    )

    @classmethod
    def from_db_model(
        cls, deck: DeckDB, include_title: bool = False, include_progress: bool = False
    ) -> "DeckResponse":
        """Create response from database model with optional fields"""
        return cls(
            deck_id=str(deck.id),
            status=deck.status,
            slide_count=len(deck.slides),
            created_at=deck.created_at,
            updated_at=deck.updated_at,
            completed_at=deck.completed_at,
            title=deck.deck_title if include_title else None,
            progress=deck.progress if include_progress else None,
            status_message=deck.status_message if include_progress else None,
        )

    @classmethod
    def for_creation(
        cls, deck_id: str, status: DeckStatus = DeckStatus.STARTING
    ) -> "DeckResponse":
        """Create response for deck creation"""
        now = datetime.now()
        return cls(
            deck_id=deck_id,
            status=status,
            slide_count=0,
            created_at=now,
        )

    @classmethod
    def for_list_item(cls, deck: DeckDB) -> "DeckResponse":
        """Create response for deck list items"""
        return cls.from_db_model(deck, include_title=True)

    @classmethod
    def for_status(cls, deck: DeckDB) -> "DeckResponse":
        """Create response for deck status"""
        return cls.from_db_model(deck, include_progress=True)


class SlideOperationResponse(BaseModel):
    """Unified response model for slide operations (modify, revert, save)"""

    deck_id: str = Field(..., description="Unique identifier of the deck")
    slide_order: int = Field(..., description="Order of the slide")
    status: str = Field(..., description="Operation status")
    message: str = Field(..., description="Human-readable message")

    # Optional fields for specific operations
    reverted_to_version: str | None = Field(
        None, description="ID of version reverted to"
    )
    version_id: str | None = Field(None, description="ID of new version created")
    version_count: int | None = Field(None, description="Total versions for this slide")

    @classmethod
    def for_modify(cls, deck_id: str, slide_order: int) -> "SlideOperationResponse":
        """Create response for slide modification"""
        return cls(
            deck_id=deck_id,
            slide_order=slide_order,
            status=DeckStatus.MODIFYING.value,
            message="Slide modification started",
        )

    @classmethod
    def for_revert(
        cls, deck_id: str, slide_order: int, version_id: str
    ) -> "SlideOperationResponse":
        """Create response for slide revert"""
        return cls(
            deck_id=deck_id,
            slide_order=slide_order,
            status="success",
            message="Slide reverted successfully",
            reverted_to_version=version_id,
        )

    @classmethod
    def for_save(
        cls, deck_id: str, slide_order: int, version_id: str, version_count: int
    ) -> "SlideOperationResponse":
        """Create response for slide save"""
        return cls(
            deck_id=deck_id,
            slide_order=slide_order,
            status="success",
            message="Slide saved successfully",
            version_id=version_id,
            version_count=version_count,
        )


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
    versions: list[SlideVersionResponse] = Field(
        ..., description="List of all versions"
    )
    current_version_id: str = Field(..., description="ID of the current version")

    @classmethod
    def from_db_slide(
        cls, deck_id: str, slide_order: int, slide: SlideDB
    ) -> "SlideVersionHistoryResponse":
        """Create response from database slide model"""
        versions = [
            SlideVersionResponse(
                version_id=version.version_id,
                content=version.content,
                timestamp=version.timestamp,
                is_current=version.is_current,
                created_by=version.created_by,
            )
            for version in (slide.versions or [])
        ]

        current_version_id = slide.content.current_version_id or ""

        return cls(
            deck_id=deck_id,
            slide_order=slide_order,
            versions=versions,
            current_version_id=current_version_id,
        )


class FileUploadResponse(BaseModel):
    """Response model for file upload"""

    filename: str = Field(..., description="Name of the uploaded file")
    content_type: str = Field(..., description="MIME type of the file")
    size: int = Field(..., description="Size of the file in bytes")
    extracted_text: str = Field(..., description="Extracted text content")
    message: str = Field(
        default="파일이 성공적으로 처리되었습니다.", description="Success message"
    )


# For backward compatibility, re-export the old names
CreateDeckResponse = DeckResponse
DeckStatusResponse = DeckResponse
DeckListItemResponse = DeckResponse
ModifySlideResponse = SlideOperationResponse
RevertSlideResponse = SlideOperationResponse
SaveSlideContentResponse = SlideOperationResponse
SlideVersion = SlideVersionResponse
SlideVersionHistory = SlideVersionHistoryResponse
