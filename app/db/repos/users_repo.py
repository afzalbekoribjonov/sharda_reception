from __future__ import annotations

from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase


class UsersRepo:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["users"]

    async def ensure_user(self, telegram_id: int) -> None:
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$setOnInsert": {"telegram_id": telegram_id, "created_at": now},
                "$set": {"updated_at": now},
            },
            upsert=True,
        )

    async def bump_start_count(self, telegram_id: int) -> int:
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$inc": {"start_count": 1},
                "$set": {"updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )
        doc = await self.col.find_one({"telegram_id": telegram_id}, {"start_count": 1})
        if not doc:
            return 0
        return int(doc.get("start_count") or 0)

    async def set_language(self, telegram_id: int, language: str) -> None:
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {"language": language, "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def get_language(self, telegram_id: int) -> str | None:
        doc = await self.col.find_one({"telegram_id": telegram_id}, {"language": 1})
        if not doc:
            return None
        return doc.get("language")
