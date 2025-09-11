from fastapi import APIRouter

from .deck import router as decks_router
from .files import router as files_router
from .health import router as health_router
from .styles import router as styles_router

# Unified API router to be mounted by the application
router = APIRouter()

# API routes
router.include_router(decks_router, prefix="/api")
router.include_router(files_router, prefix="/api")
router.include_router(styles_router, prefix="/api")

# Non-versioned operational endpoints (health/metrics-style)
router.include_router(health_router)
