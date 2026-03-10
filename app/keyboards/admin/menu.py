from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_menu_keyboard(t: dict[str, str], is_super_admin: bool) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    b.add(
        InlineKeyboardButton(text=t["btn_admin_users"], callback_data="adm:USERS"),
        InlineKeyboardButton(text=t["btn_admin_pending"], callback_data="adm:PENDING"),
        InlineKeyboardButton(text=t["btn_admin_export"], callback_data="adm:EXPORT"),
        InlineKeyboardButton(text=t["btn_admin_stats"], callback_data="adm:STATS"),
        InlineKeyboardButton(text=t["btn_admin_msg_one"], callback_data="adm:MSGONE"),
        InlineKeyboardButton(text=t["btn_admin_broadcast"], callback_data="adm:BCAST"),
    )

    if is_super_admin:
        b.add(
            InlineKeyboardButton(text=t["btn_admin_admins"], callback_data="adm:ADMINS"),
            InlineKeyboardButton(text=t["btn_admin_add_admin"], callback_data="adm:ADDADMIN"),
        )

    b.adjust(2)
    return b.as_markup()


def admin_pending_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_pending_all"], callback_data="ap:K:ALL:0"),
        InlineKeyboardButton(text=t["btn_pending_time"], callback_data="ap:K:TIME:0"),
        InlineKeyboardButton(text=t["btn_pending_creds"], callback_data="ap:K:CREDS:0"),
        InlineKeyboardButton(text=t["btn_pending_addr"], callback_data="ap:K:ADDR:0"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )
    b.adjust(2)
    return b.as_markup()


def msg_targets_keyboard(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_msg_offline"], callback_data="am:t:OFF"),
        InlineKeyboardButton(text=t["btn_msg_online"], callback_data="am:t:ON"),
        InlineKeyboardButton(text=t["btn_msg_ready"], callback_data="am:t:READY"),
        InlineKeyboardButton(text=t["btn_msg_pending"], callback_data="am:t:PENDING"),
        InlineKeyboardButton(text=t["btn_msg_one_by_phone"], callback_data="am:t:PHONE"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )
    b.adjust(2)
    return b.as_markup()


def confirm_send_keyboard(t: dict[str, str], ok_cb: str, cancel_cb: str) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(
        InlineKeyboardButton(text=t["btn_confirm_send"], callback_data=ok_cb),
        InlineKeyboardButton(text=t["btn_confirm_cancel"], callback_data=cancel_cb),
    )
    b.adjust(2)
    return b.as_markup()
