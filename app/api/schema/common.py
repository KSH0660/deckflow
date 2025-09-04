from __future__ import annotations

from typing import Any, Dict, List, Literal, Optional
from uuid import UUID
from datetime import datetime
from pydantic import BaseModel, Field, HttpUrl, ConfigDict


# --- 공통 Enum/타입 ---
DeckStatus = Literal[
    "queued", "planning", "generating", "rendering", "editing", "completed", "error"
]

TemplateType = Literal[
    "professional", "minimal", "modern", "corporate", "playful"
]

# 슬라이드/덱 공통 메타
class Pagination(BaseModel):
    model_config = ConfigDict(extra="forbid")
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


# --- 소스(참조 자료) ---
class SourceUrl(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["url"] = "url"
    url: HttpUrl
    title: Optional[str] = None
    notes: Optional[str] = None


class SourceFile(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["file"] = "file"
    file_id: str = Field(..., description="Uploaded file identifier")
    filename: Optional[str] = None
    mimetype: Optional[str] = None


class SourceText(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["text"] = "text"
    text: str = Field(..., min_length=1, max_length=200_000)
    title: Optional[str] = None


DeckSource = SourceUrl | SourceFile | SourceText


# --- 진행률/이벤트 ---
class Progress(BaseModel):
    model_config = ConfigDict(extra="forbid")
    percent: int = Field(0, ge=0, le=100)
    stage: Optional[str] = Field(None, description="planner|layout|render|edit 등 단계")
    detail: Optional[str] = None


class DeckEventOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: Literal[
        "DeckStarted",
        "SlideAdded",
        "SlideEdited",
        "SlideReordered",
        "SlideDeleted",
        "SlideRestored",
        "DeckCompleted",
        "Error",
    ]
    deck_id: UUID
    slide_id: Optional[UUID] = None
    index: Optional[int] = None
    title: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    ts: datetime = Field(default_factory=datetime.utcnow)


# --- 슬라이드/덱 출력 ---
class SlideOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    slide_id: UUID
    index: int = Field(..., ge=1)
    title: Optional[str] = None
    content_outline: Optional[str] = None
    html_content: Optional[str] = None
    presenter_notes: Optional[str] = None
    template_type: Optional[TemplateType] = None
    version_no: Optional[int] = Field(None, ge=1)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class SlideListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deck_id: UUID
    slides: List[SlideOut]
    total: int


class DeckStatusResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")
    deck_id: UUID
    status: DeckStatus
    progress: Optional[Progress] = None
    slide_count: int = 0
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
