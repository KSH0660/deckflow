import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import StreamingResponse

from app.adapter.factory import current_llm, current_repo
from app.api.schema import (
    CreateDeckRequest,
    CreateDeckResponse,
    DeckListItemResponse,
    DeckStatusResponse,
)
from app.core.config import Settings as AppSettings
from app.core.config import settings as app_settings
from app.service.export_deck import render_deck_to_html, try_render_deck_pdf
from app.service.generate_deck import generate_deck

router = APIRouter(tags=["decks"])


def get_settings() -> AppSettings:
    return app_settings


@router.post("/decks", response_model=CreateDeckResponse)
async def create_deck(req: CreateDeckRequest, s: AppSettings = Depends(get_settings)):
    """Start deck generation in background and return deck_id immediately."""
    repo = current_repo()
    deck_uuid = uuid4()

    # Save initial deck record for immediate polling
    initial = {
        "id": str(deck_uuid),
        "deck_title": req.prompt[:60] + ("..." if len(req.prompt) > 60 else ""),
        "status": "generating",
        "slides": [],
        "progress": 1,
        "step": "Queued",
        "created_at": datetime.now(),
        "updated_at": None,
        "completed_at": None,
    }
    await repo.save_deck(deck_uuid, initial)

    async def progress_cb(step: str, progress: int, _slide: dict | None = None):
        deck = await repo.get_deck(deck_uuid) or {}
        if deck.get("status") == "cancelled":
            return
        deck.update(
            {
                "status": "generating",
                "progress": int(progress),
                "step": step,
                "updated_at": datetime.now(),
            }
        )
        await repo.save_deck(deck_uuid, deck)

    # Fire-and-forget background task
    asyncio.create_task(
        generate_deck(
            prompt=req.prompt,
            llm=current_llm(model=s.llm_model),
            repo=repo,
            progress_callback=progress_cb,
            deck_id=deck_uuid,
            files=req.files,
        )
    )

    return CreateDeckResponse(deck_id=str(deck_uuid))


@router.get("/decks/{deck_id}", response_model=DeckStatusResponse)
async def get_deck_status(deck_id: UUID, s: AppSettings = Depends(get_settings)):
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    # deck is stored as dict in repositories
    return DeckStatusResponse(
        deck_id=str(deck.get("id", deck_id)),
        status=deck.get("status", "unknown"),
        slide_count=len(deck.get("slides", [])),
        progress=deck.get("progress"),
        step=deck.get("step"),
        created_at=deck.get("created_at"),
        updated_at=deck.get("updated_at"),
        completed_at=deck.get("completed_at"),
    )


@router.get("/decks", response_model=list[DeckListItemResponse])
async def list_decks(
    limit: int = Query(default=10, ge=1, le=100), s: AppSettings = Depends(get_settings)
):
    """Return recent decks with basic info."""
    repo = current_repo()
    decks = await repo.list_all_decks(limit=limit)
    # Re-shape keys if necessary; repositories already return matching keys
    return decks


@router.post("/decks/{deck_id}/cancel", response_model=DeckStatusResponse)
async def cancel_deck(deck_id: UUID, s: AppSettings = Depends(get_settings)):
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    # If already terminal, just return current state
    if deck.get("status") in {"completed", "failed", "cancelled"}:
        return DeckStatusResponse(
            deck_id=str(deck.get("id", deck_id)),
            status=deck.get("status", "unknown"),
            slide_count=len(deck.get("slides", [])),
            progress=deck.get("progress"),
            step=deck.get("step"),
            created_at=deck.get("created_at"),
            updated_at=deck.get("updated_at"),
            completed_at=deck.get("completed_at"),
        )

    deck["status"] = "cancelled"
    deck["step"] = "Cancelled by user"
    deck["updated_at"] = datetime.now()
    await repo.save_deck(deck_id, deck)

    return DeckStatusResponse(
        deck_id=str(deck.get("id", deck_id)),
        status=deck.get("status", "unknown"),
        slide_count=len(deck.get("slides", [])),
        progress=deck.get("progress"),
        step=deck.get("step"),
        created_at=deck.get("created_at"),
        updated_at=deck.get("updated_at"),
        completed_at=deck.get("completed_at"),
    )


@router.get("/decks/{deck_id}/export")
async def export_deck(
    deck_id: UUID,
    format: str = Query(default="html", pattern="^(html|pdf)$"),
    layout: str = Query(default="widescreen", pattern="^(widescreen|a4|a4-landscape)$"),
    embed: str = Query(default="inline", pattern="^(inline|iframe)$"),
    inline: bool = False,
    s: AppSettings = Depends(get_settings),
):
    """Export a deck as combined HTML or best-effort PDF."""
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

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
            detail=(
                "PDF export unavailable on server. Install 'weasyprint' or have 'wkhtmltopdf' in PATH."
            ),
        )

    disposition = "inline" if inline else "attachment"
    filename = f"{title}.pdf"
    headers = {"Content-Disposition": f'{disposition}; filename="{filename}"'}
    return StreamingResponse(
        iter([pdf_bytes]), media_type="application/pdf", headers=headers
    )


@router.get("/decks/{deck_id}/data")
async def get_deck_data(deck_id: UUID, s: AppSettings = Depends(get_settings)):
    """Return the full stored deck JSON for detailed client-side rendering.

    Note: This returns the raw stored structure which may include nested slide
    plans and rendered HTML content. Intended for first-party frontends.
    """
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    return deck
