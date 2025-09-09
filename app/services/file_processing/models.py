from pydantic import BaseModel, Field


class FileInfo(BaseModel):
    """업로드된 파일 정보"""

    filename: str
    content_type: str
    size: int
    extracted_text: str


class ChunkSummary(BaseModel):
    """청크 요약 스키마"""

    summary: str = Field(
        description="Concise summary of the chunk content in about 500 characters"
    )
