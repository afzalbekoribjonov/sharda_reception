from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.repos.admins_repo import AdminsRepo


class RoleMiddleware(BaseMiddleware):
    def __init__(self, admins_repo: AdminsRepo) -> None:
        self.admins_repo = admins_repo

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = None
        if hasattr(event, "from_user") and event.from_user:
            telegram_id = event.from_user.id

        is_admin = False
        is_super_admin = False
        if telegram_id:
            role = await self.admins_repo.get_role(telegram_id)
            is_admin = role in {"admin", "super"}
            is_super_admin = role == "super"

        data["is_admin"] = is_admin
        data["is_super_admin"] = is_super_admin
        return await handler(event, data)