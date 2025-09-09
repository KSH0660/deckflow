"""
Service layer for deck operations.

This layer handles business logic and coordinates between the API layer and data layer.
It transforms between request/response models and database models.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID, uuid4

from app.models.database.deck import DeckDB, SlideDB
from app.models.requests.deck import CreateDeckRequest, ModifySlideRequest, RevertSlideRequest
from app.models.responses.deck import (
    CreateDeckResponse,
    DeckStatusResponse,
    DeckListItemResponse,
    ModifySlideResponse,
    SlideVersionHistoryResponse,
    RevertSlideResponse,
    SaveSlideContentResponse
)


class DeckService:
    """Service for deck-related business operations"""
    
    def __init__(self, repository, llm_provider):
        self.repo = repository
        self.llm = llm_provider
    
    async def create_deck(self, request: CreateDeckRequest) -> CreateDeckResponse:
        """Create a new deck from request"""
        deck_id = uuid4()
        
        # Create initial deck record
        initial_deck = DeckDB(
            id=deck_id,
            deck_title=request.prompt[:60] + ("..." if len(request.prompt) > 60 else ""),
            status="generating",
            slides=[],
            progress=1,
            step="Queued",
            created_at=datetime.now()
        )
        
        # Save to repository (convert to dict for compatibility)
        await self.repo.save_deck(deck_id, initial_deck.to_dict())
        
        return CreateDeckResponse(deck_id=str(deck_id), status="generating")
    
    async def get_deck_status(self, deck_id: UUID) -> DeckStatusResponse:
        """Get deck status by ID"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        # Convert dict to database model
        deck = DeckDB.from_dict(deck_data)
        
        # Convert to response model
        return DeckStatusResponse.from_db_model(deck)
    
    async def list_decks(self, limit: int = 10) -> List[DeckListItemResponse]:
        """List recent decks"""
        decks_data = await self.repo.list_all_decks(limit=limit)
        
        # Convert each dict to database model, then to response model
        decks = [DeckDB.from_dict(deck_data) for deck_data in decks_data]
        return [DeckListItemResponse.from_db_model(deck) for deck in decks]
    
    async def get_deck_data(self, deck_id: UUID) -> dict:
        """Get complete deck data for rendering"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        # For now, return raw data for compatibility with existing frontend
        # In the future, this could return a structured response model
        return deck_data
    
    async def modify_slide(self, deck_id: UUID, slide_order: int, request: ModifySlideRequest) -> ModifySlideResponse:
        """Start slide modification process"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        deck = DeckDB.from_dict(deck_data)
        
        # Validate slide exists and deck is in correct state
        if deck.status not in {"completed", "modifying"}:
            raise ValueError(f"Can only modify slides in completed or modifying decks. Current status: {deck.status}")
        
        if slide_order < 1 or slide_order > len(deck.slides):
            raise ValueError("Slide not found")
        
        # Return immediate response, actual modification happens in background
        return ModifySlideResponse(
            deck_id=str(deck_id),
            slide_order=slide_order,
            status="modifying"
        )
    
    async def get_slide_version_history(self, deck_id: UUID, slide_order: int) -> SlideVersionHistoryResponse:
        """Get version history for a specific slide"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        deck = DeckDB.from_dict(deck_data)
        
        # Find the target slide
        target_slide = None
        for slide in deck.slides:
            if slide.order == slide_order:
                target_slide = slide
                break
        
        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")
        
        return SlideVersionHistoryResponse.from_db_slide(str(deck_id), slide_order, target_slide)
    
    async def revert_slide_to_version(self, deck_id: UUID, slide_order: int, request: RevertSlideRequest) -> RevertSlideResponse:
        """Revert a slide to a specific version"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        deck = DeckDB.from_dict(deck_data)
        
        # Find the target slide
        target_slide = None
        slide_index = None
        for i, slide in enumerate(deck.slides):
            if slide.order == slide_order:
                target_slide = slide
                slide_index = i
                break
        
        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")
        
        # Find the target version
        target_version = None
        if target_slide.versions:
            for version in target_slide.versions:
                if version.version_id == request.version_id:
                    target_version = version
                    break
        
        if not target_version:
            raise ValueError(f"Version {request.version_id} not found")
        
        # Update version states
        if target_slide.versions:
            for version in target_slide.versions:
                version.is_current = (version.version_id == request.version_id)
        
        # Update slide content
        target_slide.content.html_content = target_version.content
        target_slide.content.current_version_id = target_version.version_id
        target_slide.content.updated_at = datetime.now()
        
        # Update deck timestamp
        deck.updated_at = datetime.now()
        
        # Save back to repository
        await self.repo.save_deck(deck_id, deck.to_dict())
        
        return RevertSlideResponse(
            deck_id=str(deck_id),
            slide_order=slide_order,
            reverted_to_version=request.version_id,
            status="success"
        )
    
    async def save_slide_content(self, deck_id: UUID, slide_order: int, html_content: str) -> SaveSlideContentResponse:
        """Save edited HTML content with versioning"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        deck = DeckDB.from_dict(deck_data)
        
        # Find the target slide
        target_slide = None
        slide_index = None
        for i, slide in enumerate(deck.slides):
            if slide.order == slide_order:
                target_slide = slide
                slide_index = i
                break
        
        if not target_slide:
            raise ValueError(f"Slide {slide_order} not found")
        
        current_time = datetime.now()
        current_content = target_slide.content.html_content
        
        # Only create new version if content actually changed
        if current_content != html_content:
            # Initialize versions list if it doesn't exist
            if target_slide.versions is None:
                target_slide.versions = []
            
            # Mark all existing versions as not current
            for version in target_slide.versions:
                version.is_current = False
            
            # Create new version
            from app.models.database.deck import SlideVersionDB
            new_version = SlideVersionDB(
                version_id=f"v{len(target_slide.versions) + 1}_{int(current_time.timestamp())}",
                content=html_content,
                timestamp=current_time,
                is_current=True,
                created_by="user"
            )
            
            # Add new version to versions list
            target_slide.versions.append(new_version)
            
            # Keep only last 10 versions
            if len(target_slide.versions) > 10:
                target_slide.versions = target_slide.versions[-10:]
            
            # Update current content
            target_slide.content.html_content = html_content
            target_slide.content.current_version_id = new_version.version_id
            target_slide.content.updated_at = current_time
        
        # Update deck timestamp
        deck.updated_at = current_time
        
        # Save to database
        await self.repo.save_deck(deck_id, deck.to_dict())
        
        return SaveSlideContentResponse(
            status="success",
            message="편집 내용이 저장되었습니다",
            version_id=target_slide.content.current_version_id,
            version_count=len(target_slide.versions) if target_slide.versions else 0
        )
    
    async def delete_deck(self, deck_id: UUID) -> dict:
        """Delete a deck"""
        deck_data = await self.repo.get_deck(deck_id)
        if not deck_data:
            raise ValueError("Deck not found")
        
        await self.repo.delete_deck(deck_id)
        
        return {
            "status": "success",
            "message": "Deck deleted successfully",
            "deck_id": str(deck_id)
        }