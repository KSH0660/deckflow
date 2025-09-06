from fastapi import APIRouter

from .deck import router as decks_router
from .health import router as health_router


# Unified API router to be mounted by the application
router = APIRouter()

# Versioned application routes
router.include_router(decks_router, prefix="/api/v1")

# Non-versioned operational endpoints (health/metrics-style)
router.include_router(health_router)
