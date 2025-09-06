from datetime import datetime
from typing import Any
from uuid import UUID

from .base import Repository


class InMemoryRepository(Repository):
    def __init__(self):
        self._decks: dict[UUID, dict[str, Any]] = {}

    async def save_deck(self, deck_id: UUID, data: dict[str, Any]) -> None:
        self._decks[deck_id] = data

    async def get_deck(self, deck_id: UUID) -> dict[str, Any] | None:
        return self._decks.get(deck_id)

    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        if deck_id in self._decks:
            self._decks[deck_id]["status"] = status
            self._decks[deck_id]["updated_at"] = datetime.now()

    async def list_all_decks(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent decks with basic info"""
        decks = []
        for deck_id, data in self._decks.items():
            deck_info = {
                "deck_id": str(deck_id),
                "title": data.get("deck_title", "Untitled"),
                "status": data.get("status", "unknown"),
                "created_at": data.get("created_at"),
                "updated_at": data.get("updated_at"),
                "slide_count": len(data.get("slides", [])),
            }
            decks.append(deck_info)

        # Sort by created_at (newest first)
        decks.sort(key=lambda x: x.get("created_at", datetime.min), reverse=True)
        return decks[:limit]
