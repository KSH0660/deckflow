from uuid import UUID

from fastapi import APIRouter, HTTPException, Query

from app.adapter.factory import current_llm, current_repo
from app.api.schema import (
    CreateDeckRequest,
    CreateDeckResponse,
    DeckStatusResponse,
    DeckListItemResponse,
)
from app.service.generate_deck import generate_deck

router = APIRouter(tags=["decks"])


@router.post("/decks", response_model=CreateDeckResponse)
async def create_deck(req: CreateDeckRequest):
    deck_id = await generate_deck(
        prompt=req.prompt,
        llm=current_llm(),
        repo=current_repo(),
    )
    return CreateDeckResponse(deck_id=deck_id)


@router.get("/decks/{deck_id}", response_model=DeckStatusResponse)
async def get_deck_status(deck_id: UUID):
    repo = current_repo()
    deck = await repo.get_deck(deck_id)
    if not deck:
        raise HTTPException(status_code=404, detail="Deck not found")
    # deck is stored as dict in repositories
    return DeckStatusResponse(
        deck_id=str(deck.get("id", deck_id)),
        status=deck.get("status", "unknown"),
        slide_count=len(deck.get("slides", [])),
        created_at=deck.get("created_at"),
        updated_at=deck.get("updated_at"),
        completed_at=deck.get("completed_at"),
    )


@router.get("/decks", response_model=list[DeckListItemResponse])
async def list_decks(limit: int = Query(default=10, ge=1, le=100)):
    """Return recent decks with basic info."""
    repo = current_repo()
    decks = await repo.list_all_decks(limit=limit)
    # Re-shape keys if necessary; repositories already return matching keys
    return decks
