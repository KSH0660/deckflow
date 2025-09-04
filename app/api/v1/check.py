from fastapi import APIRouter
from app.core.config import settings 

router = APIRouter()


@router.get("/healthz")
async def healthz():
    """Liveness probe endpoint."""
    return {"status": "ok"}


@router.get("/meta")
async def meta():
    """Service metadata and operational configuration."""
    quality = {
        "draft": {
            "model": settings.DRAFT_MODEL,
            "max_concurrency": settings.DRAFT_MAX_CONCURRENCY,
        },
        "default": {
            "model": settings.DEFAULT_MODEL,
            "max_concurrency": settings.DEFAULT_MAX_CONCURRENCY,
        },
        "premium": {
            "model": settings.PREMIUM_MODEL,
            "max_concurrency": settings.PREMIUM_MAX_CONCURRENCY,
        },
    }
 
    return {
        "service": "presto-api",
        "version": "1.0.0",
        "quality_tiers": quality, 
    }
 