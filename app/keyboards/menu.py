from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_menu_profile"], callback_data="menu:PROFILE"),
        InlineKeyboardButton(text=t["btn_menu_exam"], callback_data="menu:EXAM"),
        InlineKeyboardButton(text=t["btn_menu_settings"], callback_data="menu:SETTINGS"),
        InlineKeyboardButton(text=t["btn_menu_sharda"], callback_data="menu:SHARDA"),
    )
    b.adjust(2)
    return b.as_markup()


def profile_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_profile_edit"], callback_data="profile:EDIT"),
        InlineKeyboardButton(text=t["btn_back"], callback_data="menu:HOME"),
    )
    b.adjust(1)
    return b.as_markup()


def settings_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_change_language"], callback_data="settings:LANG"),
        InlineKeyboardButton(text=t["btn_back_menu"], callback_data="menu:HOME"),
    )
    b.adjust(1)
    return b.as_markup()


def exam_keyboard(t: dict[str, str], has_location: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    if has_location:
        b.add(InlineKeyboardButton(text=t["btn_get_location"], callback_data="exam:LOC"))
    b.add(InlineKeyboardButton(text=t["btn_back"], callback_data="menu:HOME"))
    b.adjust(1)
    return b.as_markup()


def sharda_info_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_sharda_contact"], callback_data="sharda:CONTACT"),
        InlineKeyboardButton(text=t["btn_sharda_faculty"], callback_data="sharda:FACULTY"),
        InlineKeyboardButton(text=t["btn_sharda_back"], callback_data="sharda:BACK"),
    )
    b.adjust(1)
    return b.as_markup()
