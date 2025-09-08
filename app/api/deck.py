import asyncio
from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from fastapi.responses import StreamingResponse

from app.adapter.factory import current_llm, current_repo
from app.api.schema import (
    CreateDeckRequest,
    CreateDeckResponse,
    DeckListItemResponse,
    DeckStatusResponse,
    ModifySlideRequest,
    ModifySlideResponse,
    RevertSlideRequest,
    RevertSlideResponse,
    SlideVersion,
    SlideVersionHistory,
)
from app.core.config import Settings as AppSettings
from app.core.config import settings as app_settings
from app.service.export_deck import render_deck_to_html, try_render_deck_pdf
from app.service.modify_slide import modify_slide
from app.service.orchestration import generate_deck

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


@router.post(
    "/decks/{deck_id}/slides/{slide_order}/modify", response_model=ModifySlideResponse
)
async def modify_slide_endpoint(
    deck_id: UUID,
    slide_order: int,
    req: ModifySlideRequest,
    s: AppSettings = Depends(get_settings),
):
    """Modify a specific slide in the deck."""
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    current_status = deck.get("status")
    if current_status not in {"completed", "modifying"}:
        raise HTTPException(
            status_code=400,
            detail=f"Can only modify slides in completed or modifying decks. Current status: {current_status}",
        )

    slides = deck.get("slides", [])
    if not slides or slide_order < 1 or slide_order > len(slides):
        raise HTTPException(status_code=404, detail="Slide not found")

    async def progress_cb(step: str, progress: int, _slide: dict | None = None):
        deck = await repo.get_deck(deck_id) or {}
        if deck.get("status") == "cancelled":
            return

        # 진행률이 100%가 되면 completed 상태로 변경, 그렇지 않으면 modifying
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
            modification_prompt=req.modification_prompt,
            llm=current_llm(model=s.llm_model),
            repo=repo,
            progress_callback=progress_cb,
        )
    )

    return ModifySlideResponse(deck_id=str(deck_id), slide_order=slide_order)


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


@router.post("/save")
async def save_edited_html(
    request: Request, deck_id: str = Query(...), slide_order: int = Query(...)
):
    """Save edited HTML content from TinyMCE inline editor with versioning
        {
        "versions": [
        {
            "version_id": "v1_1694188800",
            "content": "<div>Original content</div>",
            "timestamp": "2023-09-08T...",
            "is_current": false,
            "created_by": "user"
        },
        {
            "version_id": "v2_1694189200",
            "content": "<div>Updated content</div>",
            "timestamp": "2023-09-08T...",
            "is_current": true,
            "created_by": "user"
        }
        ]
    }
    """
    try:
        # Get the raw HTML content from request body
        html_content = await request.body()
        html_str = html_content.decode("utf-8")

        # Get repository
        repo = current_repo()

        # Get current deck
        deck_uuid = UUID(deck_id)
        deck = await repo.get_deck(deck_uuid)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")

        # Find the slide to update
        slide_found = False
        current_time = datetime.now()

        for slide in deck.get("slides", []):
            if slide.get("order") == slide_order:
                # Initialize content and versions if they don't exist
                if "content" not in slide:
                    slide["content"] = {}
                if "versions" not in slide:
                    slide["versions"] = []

                # Get current content for comparison
                current_content = slide["content"].get("html_content", "")

                # Only create new version if content actually changed
                if current_content != html_str:
                    # Mark all existing versions as not current
                    for version in slide["versions"]:
                        version["is_current"] = False

                    # Create new version
                    new_version_id = (
                        f"v{len(slide['versions']) + 1}_{int(current_time.timestamp())}"
                    )
                    new_version = {
                        "version_id": new_version_id,
                        "content": html_str,
                        "timestamp": current_time.isoformat(),
                        "is_current": True,
                        "created_by": "user",
                    }

                    # Add new version to versions list
                    slide["versions"].append(new_version)

                    # Keep only last 10 versions to prevent unbounded growth
                    if len(slide["versions"]) > 10:
                        slide["versions"] = slide["versions"][-10:]

                    # Update current content
                    slide["content"]["html_content"] = html_str
                    slide["content"]["current_version_id"] = new_version_id
                    slide["content"]["updated_at"] = current_time.isoformat()

                slide_found = True
                break

        if not slide_found:
            raise HTTPException(
                status_code=404, detail=f"Slide {slide_order} not found"
            )

        # Update the deck's updated_at timestamp
        deck["updated_at"] = current_time

        # Save back to database
        await repo.save_deck(deck_uuid, deck)

        return {
            "status": "success",
            "message": "편집 내용이 저장되었습니다",
            "version_id": slide["content"].get("current_version_id"),
            "version_count": len(slide.get("versions", [])),
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"잘못된 deck_id 형식: {str(e)}"
        ) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"저장 실패: {str(e)}") from e


@router.get(
    "/decks/{deck_id}/slides/{slide_order}/versions", response_model=SlideVersionHistory
)
async def get_slide_version_history(
    deck_id: UUID, slide_order: int, s: AppSettings = Depends(get_settings)
):
    """Get version history for a specific slide"""
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    # Find the slide
    target_slide = None
    for slide in deck.get("slides", []):
        if slide.get("order") == slide_order:
            target_slide = slide
            break

    if not target_slide:
        raise HTTPException(status_code=404, detail=f"Slide {slide_order} not found")

    # Get versions, ensuring they exist
    versions = target_slide.get("versions", [])
    current_version_id = target_slide.get("content", {}).get("current_version_id", "")

    # Convert to response format
    version_objects = []
    for version in versions:
        version_objects.append(
            SlideVersion(
                version_id=version["version_id"],
                content=version["content"],
                timestamp=datetime.fromisoformat(version["timestamp"]),
                is_current=version.get("is_current", False),
                created_by=version.get("created_by", "user"),
            )
        )

    return SlideVersionHistory(
        deck_id=str(deck_id),
        slide_order=slide_order,
        versions=version_objects,
        current_version_id=current_version_id,
    )


@router.post(
    "/decks/{deck_id}/slides/{slide_order}/revert", response_model=RevertSlideResponse
)
async def revert_slide_to_version(
    deck_id: UUID,
    slide_order: int,
    request: RevertSlideRequest,
    s: AppSettings = Depends(get_settings),
):
    """Revert a slide to a specific version"""
    try:
        repo = current_repo()
        deck = await repo.get_deck(deck_id)
        if not deck:
            raise HTTPException(status_code=404, detail="Deck not found")

        # Find the slide
        target_slide = None
        for slide in deck.get("slides", []):
            if slide.get("order") == slide_order:
                target_slide = slide
                break

        if not target_slide:
            raise HTTPException(
                status_code=404, detail=f"Slide {slide_order} not found"
            )

        # Find the target version
        target_version = None
        versions = target_slide.get("versions", [])
        for version in versions:
            if version["version_id"] == request.version_id:
                target_version = version
                break

        if not target_version:
            raise HTTPException(
                status_code=404, detail=f"Version {request.version_id} not found"
            )

        # Mark all versions as not current
        for version in versions:
            version["is_current"] = False

        # Mark target version as current
        target_version["is_current"] = True

        # Update slide content
        if "content" not in target_slide:
            target_slide["content"] = {}

        target_slide["content"]["html_content"] = target_version["content"]
        target_slide["content"]["current_version_id"] = target_version["version_id"]
        target_slide["content"]["updated_at"] = datetime.now().isoformat()

        # Update deck timestamp
        deck["updated_at"] = datetime.now()

        # Save to database
        await repo.save_deck(deck_id, deck)

        return RevertSlideResponse(
            deck_id=str(deck_id),
            slide_order=slide_order,
            reverted_to_version=request.version_id,
            status="success",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"버전 되돌리기 실패: {str(e)}"
        ) from e


@router.delete("/decks/{deck_id}")
async def delete_deck(deck_id: UUID, s: AppSettings = Depends(get_settings)):
    """Delete a specific deck."""
    repo = current_repo()

    # Check if deck exists
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")

    try:
        # Delete the deck from repository
        await repo.delete_deck(deck_id)
        return {
            "status": "success",
            "message": "Deck deleted successfully",
            "deck_id": str(deck_id),
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"덱 삭제 실패: {str(e)}") from e
