from datetime import datetime

from pydantic import BaseModel, Field

# Import FileInfo from file_processing module to avoid duplication
from app.service.file_processing import FileInfo


class CreateDeckRequest(BaseModel):
    prompt: str = Field(..., min_length=5, max_length=5000)
    style: dict[str, str] | None = None
    files: list[FileInfo] | None = None


class CreateDeckResponse(BaseModel):
    deck_id: str
    status: str = "generating"


class DeckStatusResponse(BaseModel):
    deck_id: str
    status: str
    slide_count: int
    progress: int | None = None
    step: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class DeckListItemResponse(BaseModel):
    deck_id: str
    title: str
    status: str
    slide_count: int
    created_at: datetime
    updated_at: datetime | None = None
    completed_at: datetime | None = None


class ModifySlideRequest(BaseModel):
    """개별 슬라이드 수정 요청"""

    modification_prompt: str = Field(..., min_length=5, max_length=2000)


class ModifySlideResponse(BaseModel):
    """슬라이드 수정 응답"""

    deck_id: str
    slide_order: int
    status: str = "modifying"


class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""

    filename: str
    content_type: str
    size: int
    extracted_text: str
    message: str = "파일이 성공적으로 처리되었습니다."


class SlideVersion(BaseModel):
    """슬라이드 버전 정보"""

    version_id: str
    content: str
    timestamp: datetime
    is_current: bool = False
    created_by: str = "user"  # 향후 확장을 위해


class SlideVersionHistory(BaseModel):
    """슬라이드 버전 기록"""

    deck_id: str
    slide_order: int
    versions: list[SlideVersion]
    current_version_id: str


class RevertSlideRequest(BaseModel):
    """슬라이드 버전 되돌리기 요청"""

    version_id: str


class RevertSlideResponse(BaseModel):
    """슬라이드 버전 되돌리기 응답"""

    deck_id: str
    slide_order: int
    reverted_to_version: str
    status: str = "success"
