from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase


class AdminsRepo:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["admins"]

    async def ensure_super_admin(self, telegram_id: int) -> None:
        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {"role": "super", "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def get_role(self, telegram_id: int) -> str | None:
        doc = await self.col.find_one({"telegram_id": telegram_id}, {"role": 1})
        if not doc:
            return None
        return doc.get("role")

    async def is_admin(self, telegram_id: int) -> bool:
        role = await self.get_role(telegram_id)
        return role in {"admin", "super"}

    async def is_super(self, telegram_id: int) -> bool:
        role = await self.get_role(telegram_id)
        return role == "super"

    async def list_admins(self) -> list[dict[str, Any]]:
        cur = self.col.find({}, {"telegram_id": 1, "role": 1}).sort("created_at", 1)
        return await cur.to_list(length=1000)

    async def upsert_admin(self, telegram_id: int) -> None:
        """
        Promote / add user as admin (not super).
        """
        from datetime import datetime, timezone

        now = datetime.now(timezone.utc)
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {"role": "admin", "updated_at": now},
                "$setOnInsert": {"created_at": now},
            },
            upsert=True,
        )

    async def remove_admin(self, telegram_id: int) -> None:
        """
        Remove admin role (super admin should not be removed here).
        """
        await self.col.delete_one({"telegram_id": telegram_id, "role": {"$ne": "super"}})