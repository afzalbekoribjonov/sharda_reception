from __future__ import annotations

import math

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import admin_pending_list_keyboard, admin_user_detail_keyboard
from app.routers.admin._common import render_user_detail
from app.utils.edit import safe_edit_text

router = Router()


@router.callback_query(F.data.startswith("ap:"))
async def pending_router(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) >= 4 and parts[1] == "K":
        kind = parts[2]
        page = max(int(parts[3]), 0)

        total = await candidates_repo.pending_count(kind)
        pages = max(1, math.ceil(total / 10))
        if page >= pages:
            page = pages - 1

        docs = await candidates_repo.pending_list_page(kind, page, page_size=10)
        items = [(int(d.get("telegram_id")), str(d.get("full_name") or ""), str(d.get("phone") or "")) for d in docs]

        title = t["pending_list_title"].format(count=total, page=page + 1, pages=pages)

        await callback.answer()
        await safe_edit_text(
            callback.message,
            title,
            reply_markup=admin_pending_list_keyboard(items, kind, page, pages, t),
        )
        return

    if len(parts) >= 5 and parts[1] == "V":
        tid = int(parts[2])
        kind = parts[3]
        page = max(int(parts[4]), 0)

        text, exam_type = await render_user_detail(candidates_repo, t, tid)

        await callback.answer()
        await safe_edit_text(
            callback.message,
            text,
            reply_markup=admin_user_detail_keyboard(tid, return_kind=kind, return_page=page, t=t, exam_type=exam_type),
        )
        return

    await callback.answer()
