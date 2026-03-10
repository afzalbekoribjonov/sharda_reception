from __future__ import annotations
from app.config import settings
from app.keyboards.common import open_webapp_reply_keyboard
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from app.db.repos.users_repo import UsersRepo
from app.db.repos.candidates_repo import CandidatesRepo
from app.i18n.loader import SUPPORTED_LANGS
from app.keyboards.common import lang_keyboard
from app.keyboards.menu import main_menu_keyboard
from app.utils.edit import safe_edit_text
from app.utils.why_choose import maybe_send_why_choose_sharda

router = Router()


@router.message(F.text.in_({"/start", "start"}))
async def cmd_start(
    message: Message,
    users_repo: UsersRepo,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
) -> None:
    start_count = await users_repo.bump_start_count(message.from_user.id)

    status = await candidates_repo.get_status(message.from_user.id)
    if status == "registered":
        if start_count >= 2:
            await maybe_send_why_choose_sharda(message, candidates_repo, t, allow_repeat=True)
        await message.answer(t["main_menu_title"], reply_markup=main_menu_keyboard(t))
        return

    # registered emas -> til tanlash (birinchi bosqich)
    await message.answer(t["choose_lang"], reply_markup=lang_keyboard(t))


@router.callback_query(F.data.startswith("setlang:"))
async def on_set_language(
    callback: CallbackQuery,
    users_repo: UsersRepo,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
) -> None:
    lang = callback.data.split(":", 1)[1].strip()
    if lang not in SUPPORTED_LANGS:
        await callback.answer("Invalid language", show_alert=True)
        return

    await users_repo.set_language(callback.from_user.id, lang)
    await callback.answer("✅")

    # Til tanlangach: agar user ro'yxatdan o'tgan bo'lsa menyu, bo'lmasa intro
    status = await candidates_repo.get_status(callback.from_user.id)
    if status == "registered":
        await safe_edit_text(callback.message, t["main_menu_title"], reply_markup=main_menu_keyboard(t))
    else:
        if settings.WEBAPP_URL:
            await safe_edit_text(
                callback.message,
                t["webapp_hint"],
                reply_markup=None,
            )
            await callback.message.answer(
                t["btn_open_webapp"],
                reply_markup=open_webapp_reply_keyboard(t, settings.WEBAPP_URL, lang=lang),
            )
        else:
            await safe_edit_text(callback.message, t["intro_caption"], reply_markup=None)


@router.callback_query(F.data == "langback:START")
async def on_lang_back(callback: CallbackQuery, t: dict[str, str]) -> None:
    # Startdagi til tanlashdan "back" bosilsa introga qaytaramiz
    await callback.answer()
    await safe_edit_text(callback.message, t["intro_caption"], reply_markup=None)
