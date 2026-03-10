from __future__ import annotations

import asyncio

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import admin_menu_keyboard, confirm_send_keyboard
from app.routers.admin._state import AdminBcast
from app.utils.edit import safe_edit_text

router = Router()


@router.message(AdminBcast.waiting_post)
async def admin_bcast_receive_post(
    message: Message,
    state: FSMContext,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await state.clear()
        return

    tids = await candidates_repo.all_tids()
    count = len(tids)

    await state.update_data(
        from_chat_id=message.chat.id,
        from_message_id=message.message_id,
        tids=tids,
        count=count,
    )
    await state.set_state(AdminBcast.confirm)

    await message.answer(
        t["bcast_confirm"].format(count=count),
        reply_markup=confirm_send_keyboard(t, ok_cb="bc:send", cancel_cb="aa:CANCEL"),
    )


@router.callback_query(F.data == "bc:send")
async def admin_bcast_send(
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
    from_chat_id = int(data["from_chat_id"])
    from_message_id = int(data["from_message_id"])
    tids: list[int] = data.get("tids") or []
    count = len(tids)

    await callback.answer()
    await safe_edit_text(callback.message, t["msg_sending"].format(count=count), reply_markup=None)

    ok = 0
    fail = 0
    for tid in tids:
        try:
            await bot.copy_message(chat_id=tid, from_chat_id=from_chat_id, message_id=from_message_id)
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
