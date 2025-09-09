"""
Database models for deck and slide entities.

These models represent the actual data structure stored in the database.
They should be independent of API request/response formats.
"""
from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field


class SlideVersionDB(BaseModel):
    """Database model for slide version"""
    version_id: str
    content: str
    timestamp: datetime
    is_current: bool = False
    created_by: str = "user"


class SlideContentDB(BaseModel):
    """Database model for slide content"""
    html_content: str
    current_version_id: Optional[str] = None
    updated_at: Optional[datetime] = None


class SlidePlanDB(BaseModel):
    """Database model for slide plan information"""
    slide_title: str
    key_points: Optional[List[str]] = None
    data_points: Optional[List[str]] = None
    expert_insights: Optional[List[str]] = None
    layout_type: Optional[str] = None


class SlideDB(BaseModel):
    """Database model for a slide"""
    order: int
    content: SlideContentDB
    plan: SlidePlanDB
    versions: Optional[List[SlideVersionDB]] = None


class DeckDB(BaseModel):
    """Database model for a complete deck"""
    id: UUID
    deck_title: str
    status: str  # generating, completed, failed, cancelled, modifying
    slides: List[SlideDB] = Field(default_factory=list)
    
    # Progress tracking
    progress: Optional[int] = None
    step: Optional[str] = None
    
    # Metadata
    goal: Optional[str] = None
    audience: Optional[str] = None
    core_message: Optional[str] = None
    color_theme: Optional[str] = None
    
    # Timestamps
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        # Allow conversion from dict (for repository compatibility)
        extra = "forbid"
        
    @classmethod
    def from_dict(cls, data: dict) -> "DeckDB":
        """Create DeckDB from dictionary (for repository compatibility)"""
        # Convert string UUID to UUID object if needed
        if isinstance(data.get("id"), str):
            data["id"] = UUID(data["id"])
        
        # Convert slides from dict format to SlideDB objects
        if "slides" in data:
            slides_data = []
            for slide_data in data["slides"]:
                # Handle slide content
                content_data = slide_data.get("content", {})
                slide_content = SlideContentDB(**content_data)
                
                # Handle slide plan
                plan_data = slide_data.get("plan", {})
                slide_plan = SlidePlanDB(**plan_data)
                
                # Handle slide versions
                versions_data = slide_data.get("versions", [])
                slide_versions = [SlideVersionDB(**version) for version in versions_data]
                
                slide = SlideDB(
                    order=slide_data["order"],
                    content=slide_content,
                    plan=slide_plan,
                    versions=slide_versions
                )
                slides_data.append(slide)
            
            data["slides"] = slides_data
        
        return cls(**data)
    
    def to_dict(self) -> dict:
        """Convert to dictionary format (for repository compatibility)"""
        data = self.model_dump()
        # Convert UUID to string for JSON serialization
        data["id"] = str(data["id"])
        return data