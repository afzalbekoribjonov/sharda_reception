from __future__ import annotations

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from app.db.repos.users_repo import UsersRepo
from app.i18n.loader import DEFAULT_LANG, SUPPORTED_LANGS


class I18nMiddleware(BaseMiddleware):
    def __init__(self, users_repo: UsersRepo, translations: dict[str, dict[str, str]]) -> None:
        self.users_repo = users_repo
        self.translations = translations

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_id = None
        if hasattr(event, "from_user") and event.from_user:
            telegram_id = event.from_user.id

        lang = DEFAULT_LANG
        if telegram_id:
            saved = await self.users_repo.get_language(telegram_id)
            if saved in SUPPORTED_LANGS:
                lang = saved

        data["lang"] = lang
        data["t"] = self.translations[lang]
        return await handler(event, data)