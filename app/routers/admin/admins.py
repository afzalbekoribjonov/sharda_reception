from __future__ import annotations

import math

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repos.admins_repo import AdminsRepo
from app.keyboards.admin import admins_list_keyboard
from app.routers.admin._state import AdminAdd
from app.utils.edit import safe_edit_text

router = Router()


@router.message(AdminAdd.waiting_tid)
async def add_admin_receive_tid(
    message: Message,
    state: FSMContext,
    admins_repo: AdminsRepo,
    t: dict[str, str],
    is_admin: bool,
    is_super_admin: bool,
) -> None:
    if not (is_admin and is_super_admin):
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text.isdigit():
        await message.answer(t["add_admin_invalid"])
        return

    tid = int(text)
    await admins_repo.upsert_admin(tid)

    await message.answer(t["add_admin_done"].format(tid=tid))
    await state.clear()


@router.callback_query(F.data.startswith("sa:"))
async def super_admin_admins_actions(
    callback: CallbackQuery,
    admins_repo: AdminsRepo,
    t: dict[str, str],
    is_admin: bool,
    is_super_admin: bool,
) -> None:
    if not (is_admin and is_super_admin):
        await callback.answer(t["admin_only"], show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) >= 2 and parts[1] == "noop":
        await callback.answer()
        return

    page_size = 10
    admins = await admins_repo.list_admins()
    total = len(admins)
    pages = max(1, math.ceil(total / page_size))

    if parts[1] == "l":
        page = max(int(parts[2]), 0)
        if page >= pages:
            page = pages - 1

        slice_ = admins[page * page_size : (page + 1) * page_size]
        items = [(int(x["telegram_id"]), str(x.get("role") or "admin")) for x in slice_]
        title = t["admins_list_title"].format(count=total, page=page + 1, pages=pages)

        await callback.answer()
        await safe_edit_text(callback.message, title, reply_markup=admins_list_keyboard(items, page, pages, t))
        return

    if parts[1] == "rm":
        tid = int(parts[2])
        page = max(int(parts[3]), 0)

        role = None
        for x in admins:
            if int(x["telegram_id"]) == tid:
                role = x.get("role")
                break

        if role == "super":
            await callback.answer(t["remove_admin_not_allowed"], show_alert=True)
            return

        await admins_repo.remove_admin(tid)

        admins = await admins_repo.list_admins()
        total = len(admins)
        pages = max(1, math.ceil(total / page_size))
        if page >= pages:
            page = pages - 1

        slice_ = admins[page * page_size : (page + 1) * page_size]
        items = [(int(x["telegram_id"]), str(x.get("role") or "admin")) for x in slice_]
        title = t["admins_list_title"].format(count=total, page=page + 1, pages=pages)

        await callback.answer(t["remove_admin_done"].format(tid=tid), show_alert=True)
        await safe_edit_text(callback.message, title, reply_markup=admins_list_keyboard(items, page, pages, t))
        return

    await callback.answer()
