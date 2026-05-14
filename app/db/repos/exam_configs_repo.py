from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


def _now() -> datetime:
    return datetime.now(timezone.utc)


class ExamConfigsRepo:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["exam_configs"]

    async def get(self, config_id: str) -> dict[str, Any] | None:
        return await self.col.find_one({"_id": config_id})

    async def upsert(
        self,
        config_id: str,
        set_fields: dict[str, Any],
        admin_id: int,
        now: datetime | None = None,
    ) -> None:
        ts = now or _now()
        update: dict[str, Any] = {
            "$set": {**set_fields, "updated_at": ts, "updated_by_admin_id": admin_id}
        }
        await self.col.update_one({"_id": config_id}, update, upsert=True)
