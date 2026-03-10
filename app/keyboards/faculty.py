from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def faculty_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["faculty_bba"], callback_data="faculty:BBA"),
        InlineKeyboardButton(text=t["faculty_bsc"], callback_data="faculty:BSC"),
        InlineKeyboardButton(text=t["faculty_baae"], callback_data="faculty:BAAE"),
        InlineKeyboardButton(text=t["faculty_btech"], callback_data="faculty:BTECH"),
    )
    b.adjust(1)
    return b.as_markup()


def btech_tracks_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btech_cse"], callback_data="btech:CSE"),
        InlineKeyboardButton(text=t["btech_aiml"], callback_data="btech:AIML"),
        InlineKeyboardButton(text=t["btech_cyber"], callback_data="btech:CYBER"),
        InlineKeyboardButton(text=t["btn_back"], callback_data="btech:BACK"),
    )
    b.adjust(1)
    return b.as_markup()