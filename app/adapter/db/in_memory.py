from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
from uuid import UUID
from datetime import datetime

class Repository(ABC):
    @abstractmethod
    async def save_deck(self, deck_id: UUID, data: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    async def get_deck(self, deck_id: UUID) -> Optional[Dict[str, Any]]:
        pass
    
    @abstractmethod
    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        pass

class InMemoryRepository(Repository):
    def __init__(self):
        self._decks: Dict[UUID, Dict[str, Any]] = {}
    
    async def save_deck(self, deck_id: UUID, data: Dict[str, Any]) -> None:
        self._decks[deck_id] = data
    
    async def get_deck(self, deck_id: UUID) -> Optional[Dict[str, Any]]:
        return self._decks.get(deck_id)
    
    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        if deck_id in self._decks:
            self._decks[deck_id]["status"] = status
            self._decks[deck_id]["updated_at"] = datetime.now()