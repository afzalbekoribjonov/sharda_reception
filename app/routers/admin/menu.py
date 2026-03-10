from __future__ import annotations

import math

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repos.admins_repo import AdminsRepo
from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import (
    admin_filters_keyboard,
    admin_menu_keyboard,
    admin_pending_keyboard,
    admins_list_keyboard,
    export_filters_keyboard,
    msg_targets_keyboard,
)
from app.routers.admin._common import cancel_kb, export_text, filters_text
from app.routers.admin._state import AdminAdd, AdminBcast, AdminMsg
from app.utils.edit import safe_edit_text

router = Router()


@router.message(F.text.in_({"/admin", "admin"}))
async def admin_entry(message: Message, t: dict[str, str], is_admin: bool, is_super_admin: bool) -> None:
    if not is_admin:
        await message.answer(t["admin_only"])
        return
    await message.answer(t["admin_menu_title"], reply_markup=admin_menu_keyboard(t, is_super_admin=is_super_admin))


@router.callback_query(F.data.startswith("adm:"))
async def admin_menu_actions(
    callback: CallbackQuery,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    admins_repo: AdminsRepo,
    t: dict[str, str],
    is_admin: bool,
    is_super_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    action = callback.data.split(":", 1)[1]

    if action in {"HOME", "BACK"}:
        await callback.answer()
        await safe_edit_text(
            callback.message,
            t["admin_menu_title"],
            reply_markup=admin_menu_keyboard(t, is_super_admin=is_super_admin),
        )
        return

    if action == "USERS":
        await callback.answer()
        fac, ex, st = "A", "A", "A"
        await safe_edit_text(
            callback.message,
            filters_text(t, fac, ex, st),
            reply_markup=admin_filters_keyboard(fac, ex, st, t),
        )
        return

    if action.startswith("FILT:"):
        _, fac, ex, st = action.split(":")
        await callback.answer()
        await safe_edit_text(
            callback.message,
            filters_text(t, fac, ex, st),
            reply_markup=admin_filters_keyboard(fac, ex, st, t),
        )
        return

    if action == "PENDING":
        await callback.answer()
        await safe_edit_text(callback.message, t["pending_title"], reply_markup=admin_pending_keyboard(t))
        return

    if action == "EXPORT":
        await callback.answer()
        fac, ex, st, creds = "A", "A", "A", "0"
        await safe_edit_text(
            callback.message,
            export_text(t, fac, ex, st, creds),
            reply_markup=export_filters_keyboard(fac, ex, st, creds, t),
        )
        return

    if action == "STATS":
        await callback.answer()
        stats = await candidates_repo.stats()
        text = t["stats_text"].format(**stats)
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=admin_menu_keyboard(t, is_super_admin=is_super_admin),
        )
        return

    if action == "ADMINS":
        if not is_super_admin:
            await callback.answer(t["admin_only"], show_alert=True)
            return

        await callback.answer()
        admins = await admins_repo.list_admins()

        page = 0
        page_size = 10
        total = len(admins)
        pages = max(1, math.ceil(total / page_size))
        slice_ = admins[page * page_size : (page + 1) * page_size]
        items = [(int(x["telegram_id"]), str(x.get("role") or "admin")) for x in slice_]

        title = t["admins_list_title"].format(count=total, page=page + 1, pages=pages)
        await safe_edit_text(callback.message, title, reply_markup=admins_list_keyboard(items, page, pages, t))
        return

    if action == "ADDADMIN":
        if not is_super_admin:
            await callback.answer(t["admin_only"], show_alert=True)
            return

        await callback.answer()
        await state.set_state(AdminAdd.waiting_tid)
        await safe_edit_text(callback.message, t["add_admin_prompt"], reply_markup=cancel_kb(t))
        return

    if action == "MSGONE":
        await callback.answer()
        await state.clear()
        await state.set_state(AdminMsg.choosing_target)
        await safe_edit_text(callback.message, t["msg_choose_target"], reply_markup=msg_targets_keyboard(t))
        return

    if action == "BCAST":
        await callback.answer()
        await state.clear()
        await state.set_state(AdminBcast.waiting_post)
        await safe_edit_text(callback.message, t["bcast_prompt"], reply_markup=cancel_kb(t))
        return
