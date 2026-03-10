from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import admin_menu_keyboard, confirm_send_keyboard
from app.routers.admin._common import cancel_kb
from app.routers.admin._state import AdminMsg
from app.utils.edit import safe_edit_text

router = Router()


@router.callback_query(F.data.startswith("am:t:"))
async def admin_msg_choose_target(
    callback: CallbackQuery,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    _, _, kind = callback.data.split(":", 2)
    await state.update_data(kind=kind)

    if kind == "PHONE":
        await callback.answer()
        await state.set_state(AdminMsg.waiting_phone)
        await safe_edit_text(callback.message, t["msg_enter_phone"], reply_markup=cancel_kb(t))
        return

    count = await candidates_repo.target_count(kind)
    await state.update_data(count=count)
    await callback.answer()
    await state.set_state(AdminMsg.waiting_text)
    await safe_edit_text(callback.message, t["msg_enter_text"].format(count=count), reply_markup=cancel_kb(t))


@router.message(AdminMsg.waiting_phone)
async def admin_msg_phone_receive(
    message: Message,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await state.clear()
        return

    phone = (message.text or "").strip()
    doc = await candidates_repo.find_by_phone(phone)
    if not doc or not doc.get("telegram_id"):
        await message.answer(t["msg_user_not_found"])
        return

    tid = int(doc["telegram_id"])
    await state.update_data(kind="PHONE", tids=[tid], count=1, user_name=str(doc.get("full_name") or ""))
    await state.set_state(AdminMsg.waiting_text)
    await message.answer(t["msg_enter_text"].format(count=1), reply_markup=cancel_kb(t))


@router.message(AdminMsg.waiting_text)
async def admin_msg_text_receive(
    message: Message,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await state.clear()
        return

    text = (message.text or "").strip()
    if not text:
        return

    data = await state.get_data()
    kind = data.get("kind")
    count = int(data.get("count") or 0)

    if kind != "PHONE":
        tids = await candidates_repo.target_tids(kind)
        count = len(tids)
        await state.update_data(tids=tids, count=count)

    await state.update_data(msg_text=text)
    await state.set_state(AdminMsg.confirm)

    await message.answer(
        t["msg_confirm"].format(count=count),
        reply_markup=confirm_send_keyboard(t, ok_cb="am:send", cancel_cb="aa:CANCEL"),
    )


@router.callback_query(F.data == "am:send")
async def admin_msg_send(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    t: dict[str, str],
    is_admin: bool,
    is_super_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    data = await state.get_data()
    tids: list[int] = data.get("tids") or []
    msg_text: str = data.get("msg_text") or ""
    count = len(tids)

    await callback.answer()
    await safe_edit_text(callback.message, t["msg_sending"].format(count=count), reply_markup=None)

    ok = 0
    fail = 0
    for tid in tids:
        try:
            await bot.send_message(chat_id=tid, text=msg_text)
            ok += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)

    await state.clear()
    await safe_edit_text(
        callback.message,
        t["msg_done"].format(ok=ok, fail=fail),
        reply_markup=admin_menu_keyboard(t, is_super_admin=is_super_admin),
    )
