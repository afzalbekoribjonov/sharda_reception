from __future__ import annotations

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from app.keyboards.admin import admin_menu_keyboard
from app.utils.edit import safe_edit_text

router = Router()


@router.callback_query(F.data == "aa:CANCEL")
async def admin_any_cancel(
    callback: CallbackQuery,
    state: FSMContext,
    t: dict[str, str],
    is_admin: bool,
    is_super_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    await state.clear()
    await callback.answer()
    await safe_edit_text(
        callback.message,
        t["add_admin_cancel"],
        reply_markup=admin_menu_keyboard(t, is_super_admin=is_super_admin),
    )
