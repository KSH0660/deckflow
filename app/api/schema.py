from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    """파일 업로드 응답"""

    filename: str
    content_type: str
    size: int
    extracted_text: str
    message: str = "파일이 성공적으로 처리되었습니다."
