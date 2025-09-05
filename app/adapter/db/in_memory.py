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
