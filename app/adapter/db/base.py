from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID


class Repository(ABC):
    @abstractmethod
    async def save_deck(self, deck_id: UUID, data: dict[str, Any]) -> None:
        pass

    @abstractmethod
    async def get_deck(self, deck_id: UUID) -> dict[str, Any] | None:
        pass

    @abstractmethod
    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        pass
