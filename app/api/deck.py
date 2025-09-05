from fastapi import APIRouter, HTTPException
from uuid import UUID
from app.api.schema import CreateDeckRequest, CreateDeckResponse, DeckStatusResponse
from app.adapter.factory import current_llm, current_repo
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
    return DeckStatusResponse(
        deck_id=str(deck.id),
        status=deck.status,
        slide_count=len(deck.slides),
        created_at=deck.created_at,
        updated_at=deck.updated_at,
        completed_at=deck.completed_at,
    )
