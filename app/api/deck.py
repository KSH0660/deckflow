"""
Clean Architecture API Router for Deck Operations

This demonstrates proper separation of concerns:
- Request Models: Define and validate API input
- Service Layer: Handle business logic and coordinate operations
- Database Models: Represent actual data structure
- Response Models: Format API output for clients

Layers:
Request → Service → Repository → Database
Response ← Service ← Repository ← Database
"""

import asyncio
from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from app.adapter.factory import current_llm, current_repo
from app.core.config import Settings as AppSettings
from app.core.config import settings as app_settings
from app.models.requests.deck import (
    CreateDeckRequest,
    ModifySlideRequest,
    RevertSlideRequest,
)
from app.models.responses.deck import (
    CreateDeckResponse,
    DeckListItemResponse,
    DeckStatusResponse,
    ModifySlideResponse,
    RevertSlideResponse,
    SaveSlideContentResponse,
    SlideVersionHistoryResponse,
)
from app.services.deck_service import DeckService
from app.services.export.export_deck import render_deck_to_html, try_render_deck_pdf
from app.services.slide_modification.modify_slide import modify_slide

router = APIRouter(tags=["decks"])


def get_settings() -> AppSettings:
    return app_settings


def get_deck_service(
    repo=Depends(current_repo), llm=Depends(current_llm)
) -> DeckService:
    """Dependency injection for deck service"""
    return DeckService(repository=repo, llm_provider=llm)


@router.post("/decks", response_model=CreateDeckResponse)
async def create_deck(
    request: CreateDeckRequest,
    deck_service: DeckService = Depends(get_deck_service),
    settings: AppSettings = Depends(get_settings),
):
    """
    Create a new deck with clean request/response handling.

    The service layer handles ALL business logic including:
    - Database model creation
    - Repository interaction
    - Background generation orchestration
    """
    try:
        # Service handles ALL business logic - API just delegates
        return await deck_service.create_deck(request, settings)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/decks/{deck_id}", response_model=DeckStatusResponse)
async def get_deck_status(
    deck_id: UUID, deck_service: DeckService = Depends(get_deck_service)
):
    """
    Get deck status with clean error handling.

    Notice how much cleaner this is:
    - No manual field extraction
    - No dict manipulation
    - Proper error handling
    - Type safety
    """
    try:
        return await deck_service.get_deck_status(deck_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/decks", response_model=list[DeckListItemResponse])
async def list_decks(
    limit: int = Query(default=10, ge=1, le=100),
    deck_service: DeckService = Depends(get_deck_service),
):
    """List decks with proper response modeling"""
    try:
        return await deck_service.list_decks(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/decks/{deck_id}/data")
async def get_deck_data(
    deck_id: UUID, deck_service: DeckService = Depends(get_deck_service)
):
    """
    Get complete deck data for rendering.

    Note: This endpoint returns raw data for frontend compatibility.
    In a fully clean architecture, this would also have a response model.
    """
    try:
        return await deck_service.get_deck_data(deck_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/decks/{deck_id}/slides/{slide_order}/modify", response_model=ModifySlideResponse
)
async def modify_slide_endpoint(
    deck_id: UUID,
    slide_order: int,
    request: ModifySlideRequest,
    deck_service: DeckService = Depends(get_deck_service),
    settings: AppSettings = Depends(get_settings),
):
    """
    Modify a slide with proper request validation.

    The request model ensures:
    - Required fields are present
    - String length constraints
    - Input sanitization
    """
    try:
        # Validate through service layer
        response = await deck_service.modify_slide(deck_id, slide_order, request)

        # Start background modification (existing logic)
        repo = current_repo()

        async def progress_cb(step: str, progress: int, _slide: dict | None = None):
            deck = await repo.get_deck(deck_id) or {}
            if deck.get("status") == "cancelled":
                return

            if progress >= 100:
                deck.update(
                    {
                        "status": "completed",
                        "progress": None,
                        "step": None,
                        "updated_at": datetime.now(),
                    }
                )
            else:
                deck.update(
                    {
                        "status": "modifying",
                        "progress": int(progress),
                        "step": step,
                        "updated_at": datetime.now(),
                    }
                )
            await repo.save_deck(deck_id, deck)

        # Fire-and-forget background task
        asyncio.create_task(
            modify_slide(
                deck_id=deck_id,
                slide_order=slide_order,
                modification_prompt=request.modification_prompt,
                llm=current_llm(model=settings.llm_model),
                repo=repo,
                progress_callback=progress_cb,
            )
        )

        return response

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get(
    "/decks/{deck_id}/slides/{slide_order}/versions",
    response_model=SlideVersionHistoryResponse,
)
async def get_slide_version_history(
    deck_id: UUID,
    slide_order: int,
    deck_service: DeckService = Depends(get_deck_service),
):
    """
    Get slide version history with clean response modeling.

    Compare this to the original - much cleaner:
    - No manual response construction
    - Proper error handling
    - Type-safe response
    """
    try:
        return await deck_service.get_slide_version_history(deck_id, slide_order)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post(
    "/decks/{deck_id}/slides/{slide_order}/revert", response_model=RevertSlideResponse
)
async def revert_slide_to_version(
    deck_id: UUID,
    slide_order: int,
    request: RevertSlideRequest,
    deck_service: DeckService = Depends(get_deck_service),
):
    """Revert slide to version with proper request/response handling"""
    try:
        return await deck_service.revert_slide_to_version(deck_id, slide_order, request)
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e)) from e
        else:
            raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"버전 되돌리기 실패: {str(e)}"
        ) from e


@router.post("/save", response_model=SaveSlideContentResponse)
async def save_edited_html(
    request: Request,
    deck_id: str = Query(...),
    slide_order: int = Query(...),
    deck_service: DeckService = Depends(get_deck_service),
):
    """
    Save edited HTML with proper content handling.

    This endpoint maintains compatibility with the existing frontend
    while using the clean service layer underneath.
    """
    try:
        # Get HTML content from request body
        html_content = await request.body()
        html_str = html_content.decode("utf-8")

        # Validate inputs
        if not html_str.strip():
            raise HTTPException(status_code=400, detail="HTML content cannot be empty")

        deck_uuid = UUID(deck_id)
        response = await deck_service.save_slide_content(
            deck_uuid, slide_order, html_str
        )

        return response

    except ValueError as e:
        if "invalid" in str(e).lower():
            raise HTTPException(
                status_code=400, detail=f"잘못된 deck_id 형식: {str(e)}"
            ) from e
        else:
            raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}") from e


@router.post("/decks/{deck_id}/cancel", response_model=DeckStatusResponse)
async def cancel_deck(
    deck_id: UUID, deck_service: DeckService = Depends(get_deck_service)
):
    """Cancel deck generation"""
    try:
        deck_status = await deck_service.get_deck_status(deck_id)

        # If already terminal, just return current state
        if deck_status.status in {"completed", "failed", "cancelled"}:
            return deck_status

        # Update status in repository (using existing logic for now)
        repo = current_repo()
        deck = await repo.get_deck(deck_id)
        if deck:
            deck["status"] = "cancelled"
            deck["step"] = "Cancelled by user"
            deck["updated_at"] = datetime.now()
            await repo.save_deck(deck_id, deck)

        return await deck_service.get_deck_status(deck_id)

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: UUID, deck_service: DeckService = Depends(get_deck_service)
):
    """Delete a deck"""
    try:
        return await deck_service.delete_deck(deck_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"덱 삭제 실패: {str(e)}") from e


# Export endpoints (keeping existing logic for now)
@router.get("/decks/{deck_id}/export")
async def export_deck(
    deck_id: UUID,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
    layout: str = Query(default="widescreen", pattern="^(widescreen|a4|a4-landscape)$"),
    embed: str = Query(default="inline", pattern="^(inline|iframe)$"),
    inline: bool = False,
    deck_service: DeckService = Depends(get_deck_service),
):
    """Export deck with existing logic (could be refactored later)"""
    try:
        # Get deck data through service
        deck = await deck_service.get_deck_data(deck_id)

        html = render_deck_to_html(deck, layout=layout, embed=embed)
        title = deck.get("deck_title", str(deck_id))

        if format == "html":
            disposition = "inline" if inline else "attachment"
            filename = f"{title}.html"
            headers = {"Content-Disposition": f'{disposition}; filename="{filename}"'}
            return Response(
                content=html, media_type="text/html; charset=utf-8", headers=headers
            )

        pdf_bytes = try_render_deck_pdf(html, layout=layout)
        if not pdf_bytes:
            raise HTTPException(
                status_code=501,
                detail="PDF export unavailable on server. Install 'weasyprint' or have 'wkhtmltopdf' in PATH.",
            )

        disposition = "inline" if inline else "attachment"
        filename = f"{title}.pdf"
        headers = {"Content-Disposition": f'{disposition}; filename="{filename}"'}
        return StreamingResponse(
            iter([pdf_bytes]), media_type="application/pdf", headers=headers
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
