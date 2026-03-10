from __future__ import annotations

import math

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import admin_filters_keyboard, admin_list_keyboard, admin_user_detail_keyboard
from app.routers.admin._common import filters_text, render_user_detail
from app.utils.edit import safe_edit_text

router = Router()


@router.callback_query(F.data.startswith("af:"))
async def admin_filters_update(callback: CallbackQuery, t: dict[str, str], is_admin: bool) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    _, field, value, fac, ex, st = callback.data.split(":", 5)

    if field == "fac":
        fac = value
    elif field == "ex":
        ex = value
    elif field == "st":
        st = value

    await callback.answer()
    await safe_edit_text(
        callback.message,
        filters_text(t, fac, ex, st),
        reply_markup=admin_filters_keyboard(fac, ex, st, t),
    )


@router.callback_query(F.data.startswith("au:l:"))
async def admin_users_list(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) == 6:
        _, _, fac, ex, st, page_s = parts
    elif len(parts) == 4 and parts[2] == "RET":
        fac, ex, st = "A", "A", "A"
        page_s = parts[3]
    else:
        await callback.answer("Invalid", show_alert=True)
        return
    page = max(int(page_s), 0)

    total = await candidates_repo.admin_count(fac, ex, st)
    pages = max(1, math.ceil(total / 10))
    if page >= pages:
        page = pages - 1

    docs = await candidates_repo.admin_list_page(fac, ex, st, page, page_size=10)
    items = [(int(d.get("telegram_id")), str(d.get("full_name") or ""), str(d.get("phone") or "")) for d in docs]

    title = t["admin_list_title"].format(count=total, page=page + 1, pages=pages)

    await callback.answer()
    await safe_edit_text(
        callback.message,
        title,
        reply_markup=admin_list_keyboard(items, fac, ex, st, page, pages, t),
    )


@router.callback_query(F.data.startswith("au:v:"))
async def admin_user_view_from_list(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    _, _, tid_s, fac, ex, st, page_s = callback.data.split(":", 6)
    tid = int(tid_s)
    page = max(int(page_s), 0)

    text, exam_type = await render_user_detail(candidates_repo, t, tid)

    await callback.answer()
    await safe_edit_text(
        callback.message,
        text,
        reply_markup=admin_user_detail_keyboard(
            tid,
            return_kind="LIST",
            return_page=page,
            t=t,
            exam_type=exam_type,
            return_fac=fac,
            return_ex=ex,
            return_st=st,
        ),
    )
