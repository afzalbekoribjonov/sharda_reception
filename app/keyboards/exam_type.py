from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def exam_type_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_exam_online"], callback_data="exam:ONLINE"),
        InlineKeyboardButton(text=t["btn_exam_offline"], callback_data="exam:OFFLINE"),
    )
    b.adjust(2)
    return b.as_markup()