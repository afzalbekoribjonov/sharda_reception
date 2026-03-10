from __future__ import annotations

from aiogram.types import Message

from app.db.repos.candidates_repo import CandidatesRepo

WHY_CHOOSE_SHARDA_PHOTO = "https://t.me/sh_suuz_images/17"


async def maybe_send_why_choose_sharda(
    message: Message,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    *,
    allow_repeat: bool = False,
) -> bool:
    telegram_id = message.from_user.id if message.from_user else None
    if not telegram_id:
        return False

    if not allow_repeat:
        if await candidates_repo.is_why_choose_sharda_sent(telegram_id):
            return False

    await message.answer_photo(
        photo=WHY_CHOOSE_SHARDA_PHOTO,
        caption=t["why_choose_sharda_caption"],
    )
    if not allow_repeat:
        await candidates_repo.mark_why_choose_sharda_sent(telegram_id)
    return True
