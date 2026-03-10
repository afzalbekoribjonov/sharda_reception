from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo
from app.keyboards.admin import admin_user_detail_keyboard
from app.routers.admin._common import render_user_detail
from app.routers.admin._state import AdminEdit, EditCtx
from app.utils.edit import safe_edit_text
from app.utils.time import parse_exam_datetime

router = Router()


@router.callback_query(F.data.startswith("ae:"))
async def admin_edit_start(
    callback: CallbackQuery,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 5:
        await callback.answer("Invalid", show_alert=True)
        return
    _, field, tid_s, return_kind, return_page_s = parts[:5]
    tid = int(tid_s)
    return_page = int(return_page_s)
    return_fac = return_ex = return_st = None
    if return_kind == "LIST" and len(parts) >= 8:
        return_fac, return_ex, return_st = parts[5:8]

    if field in {"ADDR", "LOC", "LINK", "LOGIN", "PASS"}:
        doc = await candidates_repo.get_progress(tid)
        ex = (doc or {}).get("exam_type")
        if ex == "ONLINE" and field in {"ADDR", "LOC"}:
            await callback.answer(t["admin_edit_not_allowed_online"], show_alert=True)
            return
        if ex == "OFFLINE" and field in {"LINK", "LOGIN", "PASS"}:
            await callback.answer(t["admin_edit_not_allowed_offline"], show_alert=True)
            return

    prompt_key = {
        "TIME": "admin_enter_time",
        "ADDR": "admin_enter_address",
        "LOC": "admin_enter_location",
        "LINK": "admin_enter_link",
        "LOGIN": "admin_enter_login",
        "PASS": "admin_enter_password",
    }.get(field)

    if not prompt_key:
        await callback.answer("Invalid", show_alert=True)
        return

    ctx = EditCtx(
        field=field,
        candidate_id=tid,
        return_kind=return_kind,
        return_page=return_page,
        return_fac=return_fac,
        return_ex=return_ex,
        return_st=return_st,
        origin_chat_id=callback.message.chat.id,
        origin_message_id=callback.message.message_id,
    )

    await state.set_state(AdminEdit.waiting_value)
    await state.update_data(edit_ctx=ctx.__dict__)

    await callback.answer()
    await safe_edit_text(callback.message, t[prompt_key], reply_markup=None)


@router.message(AdminEdit.waiting_value)
async def admin_edit_receive(
    message: Message,
    bot: Bot,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    users_repo: UsersRepo,
    translations: dict[str, dict[str, str]],
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await state.clear()
        return

    data = await state.get_data()
    raw = data.get("edit_ctx") or {}
    ctx = EditCtx(**raw)

    admin_id = message.from_user.id
    if ctx.field in {"ADDR", "LOC", "LINK", "LOGIN", "PASS"}:
        doc = await candidates_repo.get_progress(ctx.candidate_id)
        ex = (doc or {}).get("exam_type")
        if ex == "ONLINE" and ctx.field in {"ADDR", "LOC"}:
            await message.answer(t["admin_edit_not_allowed_online"])
            return
        if ex == "OFFLINE" and ctx.field in {"LINK", "LOGIN", "PASS"}:
            await message.answer(t["admin_edit_not_allowed_offline"])
            return

    val = (message.text or "").strip()

    if ctx.field == "TIME":
        if not val:
            await message.answer("Empty value.")
            return
        try:
            dt_utc = parse_exam_datetime(val, settings.TZ)
        except Exception:
            await message.answer(t["admin_enter_time_invalid"])
            return
        await candidates_repo.set_exam_datetime(ctx.candidate_id, val, dt_utc, admin_id)
    elif ctx.field == "ADDR":
        if not val:
            await message.answer("Empty value.")
            return
        await candidates_repo.set_offline_address(ctx.candidate_id, val, admin_id)
    elif ctx.field == "LINK":
        if not val:
            await message.answer("Empty value.")
            return
        await candidates_repo.set_online_link(ctx.candidate_id, val, admin_id)
    elif ctx.field == "LOGIN":
        if not val:
            await message.answer("Empty value.")
            return
        await candidates_repo.set_online_login(ctx.candidate_id, val, admin_id)
    elif ctx.field == "PASS":
        if not val:
            await message.answer("Empty value.")
            return
        await candidates_repo.set_online_password(ctx.candidate_id, val, admin_id)
    elif ctx.field == "LOC":
        if message.location:
            lat = float(message.location.latitude)
            lng = float(message.location.longitude)
        else:
            if not val:
                await message.answer(t["admin_enter_location"])
                return
            try:
                lat_s, lng_s = [x.strip() for x in val.split(",", 1)]
                lat = float(lat_s)
                lng = float(lng_s)
            except Exception:
                await message.answer("Invalid location format. Use: lat,lng")
                return
        await candidates_repo.set_offline_location(ctx.candidate_id, lat, lng, admin_id)

    user_lang = await users_repo.get_language(ctx.candidate_id) or "uz"
    ut = translations.get(user_lang, translations["uz"])
    try:
        await bot.send_message(ctx.candidate_id, ut["exam_info_updated_user"])
    except Exception:
        pass

    text, exam_type = await render_user_detail(candidates_repo, t, ctx.candidate_id)

    kb = admin_user_detail_keyboard(
        ctx.candidate_id,
        ctx.return_kind,
        ctx.return_page,
        t,
        exam_type,
        return_fac=ctx.return_fac,
        return_ex=ctx.return_ex,
        return_st=ctx.return_st,
    )
    await bot.edit_message_text(
        chat_id=ctx.origin_chat_id,
        message_id=ctx.origin_message_id,
        text=text,
        reply_markup=kb,
    )

    await message.answer(t["admin_saved"])
    await state.clear()
