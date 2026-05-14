from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_exam_configs_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    b.add(
        InlineKeyboardButton(text=t["btn_exam_online"], callback_data="aex:V:ONLINE"),
        InlineKeyboardButton(text=t["btn_exam_offline"], callback_data="aex:V:OFFLINE"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )

    b.adjust(2)
    return b.as_markup()
