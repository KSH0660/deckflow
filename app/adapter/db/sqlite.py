import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from .base import Repository


class SQLiteRepository(Repository):
    def __init__(self, db_path: str = "decks.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decks (
                    deck_id TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT
                )
            """)
            conn.commit()

    async def save_deck(self, deck_id: UUID, data: dict[str, Any]) -> None:
        data_json = json.dumps(data, default=str)
        now = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO decks (deck_id, data, created_at, updated_at)
                VALUES (?, ?, ?, ?)
            """, (str(deck_id), data_json, now, now))
            conn.commit()

    async def get_deck(self, deck_id: UUID) -> dict[str, Any] | None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT data FROM decks WHERE deck_id = ?",
                (str(deck_id),)
            )
            row = cursor.fetchone()

            if row:
                return json.loads(row[0])
            return None

    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        deck_data = await self.get_deck(deck_id)
        if deck_data:
            deck_data["status"] = status
            deck_data["updated_at"] = datetime.now()
            await self.save_deck(deck_id, deck_data)
