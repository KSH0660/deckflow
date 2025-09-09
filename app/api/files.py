from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.api.schema import FileUploadResponse
from app.logging import get_logger
from app.services.file_processing.file_processor import FileProcessor, FileStorage

router = APIRouter(tags=["files"])

# 파일 저장소 인스턴스
file_storage = FileStorage()
logger = get_logger(__name__)


@router.post("/files/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """파일 업로드 및 텍스트 추출 엔드포인트"""

    logger.info(
        "📤 [FILE_UPLOAD] 파일 업로드 요청 시작",
        filename=file.filename,
        content_type=file.content_type,
    )

    # 파일 유효성 검사
    if not file.filename:
        logger.warning("📤 [FILE_UPLOAD] 파일명이 없는 업로드 요청")
        raise HTTPException(status_code=400, detail="파일명이 필요합니다.")

    # 허용된 파일 타입 확인
    if not FileProcessor.is_allowed_file(file.filename):
        logger.warning(
            "📤 [FILE_UPLOAD] 지원하지 않는 파일 형식",
            filename=file.filename,
            allowed_extensions=list(FileProcessor.ALLOWED_EXTENSIONS),
        )
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 파일 형식입니다. 허용된 확장자: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}",
        )

    # 파일 크기 확인
    file_content = await file.read()
    file_size = len(file_content)
    logger.debug(
        "📤 [FILE_UPLOAD] 파일 읽기 완료",
        filename=file.filename,
        file_size_bytes=file_size,
        file_size_kb=round(file_size / 1024, 2),
    )

    if not FileProcessor.is_valid_size(file_size):
        logger.warning(
            "📤 [FILE_UPLOAD] 파일 크기 초과",
            filename=file.filename,
            file_size_mb=round(file_size / (1024 * 1024), 2),
            max_size_mb=FileProcessor.MAX_FILE_SIZE // (1024 * 1024),
        )
        raise HTTPException(
            status_code=413,
            detail=f"파일 크기가 너무 큽니다. 최대 {FileProcessor.MAX_FILE_SIZE // (1024*1024)}MB까지 지원합니다.",
        )

    try:
        # 텍스트 추출
        logger.info("📤 [FILE_UPLOAD] 텍스트 추출 시작", filename=file.filename)
        extracted_text = await FileProcessor.extract_text(file_content, file.filename)

        # 파일 저장 (선택사항 - 필요시 주석 해제)
        # saved_path = file_storage.save_file(file.filename, file_content)

        response = FileUploadResponse(
            filename=file.filename,
            content_type=file.content_type or "application/octet-stream",
            size=file_size,
            extracted_text=extracted_text,
            message="파일이 성공적으로 처리되었습니다.",
        )

        logger.info(
            "✅ [FILE_UPLOAD] 파일 업로드 및 처리 완료",
            filename=file.filename,
            file_size_kb=round(file_size / 1024, 2),
            extracted_text_length=len(extracted_text),
            content_type=file.content_type,
        )

        return response

    except ValueError as e:
        logger.error(
            "📤 [FILE_UPLOAD] 파일 검증 오류", filename=file.filename, error=str(e)
        )
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error(
            "📤 [FILE_UPLOAD] 파일 처리 중 예상치 못한 오류",
            filename=file.filename,
            error=str(e),
        )
        raise HTTPException(
            status_code=500, detail=f"파일 처리 중 오류가 발생했습니다: {str(e)}"
        ) from e


@router.post("/files/validate")
async def validate_file(file: UploadFile = File(...)):
    """파일 유효성만 검사하는 엔드포인트"""

    if not file.filename:
        return JSONResponse(
            status_code=400, content={"valid": False, "message": "파일명이 필요합니다."}
        )

    # 허용된 파일 타입 확인
    if not FileProcessor.is_allowed_file(file.filename):
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "message": f"지원하지 않는 파일 형식입니다. 허용된 확장자: {', '.join(FileProcessor.ALLOWED_EXTENSIONS)}",
            },
        )

    # 파일 크기 확인
    file_content = await file.read()
    if not FileProcessor.is_valid_size(len(file_content)):
        return JSONResponse(
            status_code=400,
            content={
                "valid": False,
                "message": f"파일 크기가 너무 큽니다. 최대 {FileProcessor.MAX_FILE_SIZE // (1024*1024)}MB까지 지원합니다.",
            },
        )

    return JSONResponse(
        content={
            "valid": True,
            "filename": file.filename,
            "content_type": file.content_type,
            "size": len(file_content),
            "message": "파일이 유효합니다.",
        }
    )
