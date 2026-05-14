from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.config import settings
from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo
from app.keyboards.admin.bulk_edit import bulk_edit_filters_keyboard, bulk_edit_fields_keyboard
from app.routers.admin._common import bulk_filters_text, cancel_kb
from app.routers.admin._state import AdminBulkEdit, BulkEditCtx
from app.utils.edit import safe_edit_text
from app.utils.time import parse_exam_datetime

router = Router()

@router.callback_query(F.data == "adm:BULK_EDIT")
async def bulk_edit_entry(callback: CallbackQuery, t: dict[str, str], is_admin: bool) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return
    
    fac, ex = "A", "A"
    await safe_edit_text(
        callback.message,
        bulk_filters_text(t, fac, ex),
        reply_markup=bulk_edit_filters_keyboard(fac, ex, t),
    )

@router.callback_query(F.data.startswith("be:"))
async def bulk_edit_actions(
    callback: CallbackQuery,
    state: FSMContext,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    parts = callback.data.split(":")
    action = parts[1]

    if action == "fac":
        _, _, sub, fac, ex = parts
        new_fac = sub
        await safe_edit_text(
            callback.message,
            bulk_filters_text(t, new_fac, ex),
            reply_markup=bulk_edit_filters_keyboard(new_fac, ex, t),
        )
        return

    if action == "ex":
        _, _, sub, fac, ex = parts
        new_ex = sub
        await safe_edit_text(
            callback.message,
            bulk_filters_text(t, fac, new_ex),
            reply_markup=bulk_edit_filters_keyboard(fac, new_ex, t),
        )
        return

    if action == "fields":
        _, _, fac, ex = parts
        await safe_edit_text(
            callback.message,
            bulk_filters_text(t, fac, ex) + "\n\n" + t["bulk_edit_choose_field"],
            reply_markup=bulk_edit_fields_keyboard(fac, ex, t),
        )
        return

    if action == "edit":
        _, _, field, fac, ex = parts
        
        prompt_key = {
            "TIME": "admin_enter_time",
            "ADDR": "admin_enter_address",
            "LOC": "admin_enter_location",
            "LINK": "admin_enter_link",
            "LOGIN": "admin_enter_login",
            "PASS": "admin_enter_password",
        }.get(field)

        ctx = BulkEditCtx(
            field=field,
            fac=fac,
            ex=ex,
            origin_chat_id=callback.message.chat.id,
            origin_message_id=callback.message.message_id,
        )

        await state.set_state(AdminBulkEdit.waiting_value)
        await state.update_data(bulk_edit_ctx=ctx.__dict__)

        await callback.answer()
        await safe_edit_text(callback.message, t[prompt_key], reply_markup=cancel_kb(t))

@router.message(AdminBulkEdit.waiting_value)
async def admin_bulk_edit_receive(
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
    raw = data.get("bulk_edit_ctx") or {}
    ctx = BulkEditCtx(**raw)

    admin_id = message.from_user.id
    val = (message.text or "").strip()
    
    set_fields = {}
    
    if ctx.field == "TIME":
        try:
            dt_utc = parse_exam_datetime(val, settings.TZ)
            set_fields = {"exam_date_time": val, "exam_datetime_utc": dt_utc, "reminder_30m_sent": False, "reminder_30m_sent_at": None}
        except Exception:
            await message.answer(t["admin_enter_time_invalid"])
            return
    elif ctx.field == "ADDR":
        set_fields = {"address": val}
    elif ctx.field == "LINK":
        set_fields = {"online_link": val}
    elif ctx.field == "LOGIN":
        set_fields = {"exam_login": val}
    elif ctx.field == "PASS":
        set_fields = {"exam_password": val}
    elif ctx.field == "LOC":
        if message.location:
            set_fields = {"location": {"lat": float(message.location.latitude), "lng": float(message.location.longitude)}}
        else:
            try:
                lat_s, lng_s = [x.strip() for x in val.split(",", 1)]
                set_fields = {"location": {"lat": float(lat_s), "lng": float(lng_s)}}
            except Exception:
                await message.answer("Invalid location format. Use: lat,lng")
                return

    count = await candidates_repo.bulk_update_candidates(ctx.fac, ctx.ex, set_fields, admin_id)
    
    # Notify users
    tids = await candidates_repo.get_tids_by_filter(ctx.fac, ctx.ex)
    for tid in tids:
        user_lang = await users_repo.get_language(tid) or "uz"
        ut = translations.get(user_lang, translations["uz"])
        try:
            await bot.send_message(tid, ut["exam_info_updated_user"])
        except Exception:
            pass

    await message.answer(t["bulk_edit_done"].format(count=count))
    
    # Return to menu
    await bot.edit_message_text(
        chat_id=ctx.origin_chat_id,
        message_id=ctx.origin_message_id,
        text=bulk_filters_text(t, ctx.fac, ctx.ex),
        reply_markup=bulk_edit_filters_keyboard(ctx.fac, ctx.ex, t),
    )
    
    await state.clear()
