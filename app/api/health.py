from __future__ import annotations

import shutil
from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.core.config import settings as s
from app.adapter.factory import current_repo


router = APIRouter(tags=["health"])


@router.get("/healthz")
async def healthz():
    return {"status": "ok", "service": "DeckFlow", "version": "0.1.0"}


@router.get("/readyz")
async def readyz():
    """Readiness check for infra dependencies and optional tooling."""
    repo_ready = True
    repo_error: str | None = None
    try:
        repo = current_repo()
        await repo.list_all_decks(limit=1)
    except Exception as e:
        repo_ready = False
        repo_error = str(e)

    llm_ready = bool(s.openai_api_key)

    try:
        import weasyprint  # type: ignore  # noqa: F401

        weasyprint_available = True
    except Exception:
        weasyprint_available = False

    try:
        import playwright.sync_api  # type: ignore  # noqa: F401

        playwright_available = True
    except Exception:
        playwright_available = False

    wkhtmltopdf_available = shutil.which("wkhtmltopdf") is not None

    pdf_any = any([weasyprint_available, wkhtmltopdf_available, playwright_available])

    status = "ok" if (repo_ready and llm_ready) else ("degraded" if repo_ready else "error")
    http_code = 200 if status == "ok" else 503

    payload = {
        "status": status,
        "service": "DeckFlow",
        "version": "0.1.0",
        "repo_backend": s.repo,
        "repo_ready": repo_ready,
        "repo_error": repo_error,
        "llm_ready": llm_ready,
        "pdf": {
            "available": pdf_any,
            "playwright": playwright_available,
            "weasyprint": weasyprint_available,
            "wkhtmltopdf": wkhtmltopdf_available,
        },
    }

    return JSONResponse(content=payload, status_code=http_code)

