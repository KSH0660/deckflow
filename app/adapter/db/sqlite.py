import json
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import aiosqlite

from app.logging import get_logger

from .base import Repository

logger = get_logger(__name__)


class SQLiteRepository(Repository):
    def __init__(self, db_path: str = "decks.db"):
        self.db_path = db_path

    async def _init_db(self) -> None:
        """Initialize database and create tables if they don't exist."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    CREATE TABLE IF NOT EXISTS decks (
                        deck_id TEXT PRIMARY KEY,
                        data TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                    """
                )
                await db.commit()
                logger.info("SQLite 데이터베이스 초기화 완료", db_path=self.db_path)

        except Exception as e:
            logger.error("SQLite 데이터베이스 초기화 실패", error=str(e), db_path=self.db_path)
            raise

    async def save_deck(self, deck_id: UUID, data: dict[str, Any]) -> None:
        """Save deck data to database."""
        try:
            # Ensure database is initialized
            await self._init_db()

            data_json = json.dumps(data, default=str)
            now = datetime.now().isoformat()

            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO decks (deck_id, data, created_at, updated_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (str(deck_id), data_json, now, now),
                )
                await db.commit()

            logger.debug("덱 저장 완료", deck_id=str(deck_id), data_size=len(data_json))

        except json.JSONEncodeError as e:
            logger.error("덱 데이터 JSON 직렬화 실패", deck_id=str(deck_id), error=str(e))
            raise ValueError(f"Invalid data format for deck {deck_id}: {e}") from e
        except Exception as e:
            logger.error("덱 저장 실패", deck_id=str(deck_id), error=str(e))
            raise

    async def get_deck(self, deck_id: UUID) -> dict[str, Any] | None:
        """Retrieve deck data from database."""
        try:
            # Ensure database is initialized
            await self._init_db()

            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    "SELECT data FROM decks WHERE deck_id = ?", (str(deck_id),)
                )
                row = await cursor.fetchone()

                if row:
                    deck_data = json.loads(row[0])
                    logger.debug("덱 조회 완료", deck_id=str(deck_id))
                    return deck_data

                logger.debug("덱을 찾을 수 없음", deck_id=str(deck_id))
                return None

        except json.JSONDecodeError as e:
            logger.error("덱 데이터 JSON 파싱 실패", deck_id=str(deck_id), error=str(e))
            raise ValueError(f"Corrupted data for deck {deck_id}: {e}") from e
        except Exception as e:
            logger.error("덱 조회 실패", deck_id=str(deck_id), error=str(e))
            raise

    async def update_deck_status(self, deck_id: UUID, status: str) -> None:
        """Update deck status in database."""
        try:
            deck_data = await self.get_deck(deck_id)
            if deck_data is None:
                logger.warning("상태 업데이트할 덱을 찾을 수 없음", deck_id=str(deck_id))
                raise ValueError(f"Deck {deck_id} not found")

            deck_data["status"] = status
            deck_data["updated_at"] = datetime.now().isoformat()
            await self.save_deck(deck_id, deck_data)

            logger.debug("덱 상태 업데이트 완료", deck_id=str(deck_id), status=status)

        except Exception as e:
            logger.error("덱 상태 업데이트 실패", deck_id=str(deck_id), status=status, error=str(e))
            raise
    
    async def list_all_decks(self, limit: int = 10) -> list[dict[str, Any]]:
        """List recent decks with basic info"""
        try:
            await self._init_db()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    """
                    SELECT deck_id, data, created_at, updated_at 
                    FROM decks 
                    ORDER BY created_at DESC 
                    LIMIT ?
                    """,
                    (limit,)
                )
                rows = await cursor.fetchall()
                
                decks = []
                for row in rows:
                    deck_id, data_json, created_at, updated_at = row
                    try:
                        data = json.loads(data_json)
                        deck_info = {
                            "deck_id": deck_id,
                            "title": data.get("deck_title", "Untitled"),
                            "status": data.get("status", "unknown"),
                            "created_at": created_at,
                            "updated_at": updated_at,
                            "slide_count": len(data.get("slides", []))
                        }
                        decks.append(deck_info)
                    except json.JSONDecodeError:
                        logger.warning("덱 데이터 파싱 실패, 스킵", deck_id=deck_id)
                        continue
                
                logger.debug("덱 목록 조회 완료", count=len(decks))
                return decks
                
        except Exception as e:
            logger.error("덱 목록 조회 실패", error=str(e))
            raise
