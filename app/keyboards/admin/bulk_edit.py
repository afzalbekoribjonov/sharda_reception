from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def bulk_edit_filters_keyboard(fac: str, ex: str, t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    # Faculty filters
    b.add(
        InlineKeyboardButton(text=t["btn_filter_fac_any"], callback_data=f"be:fac:A:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bba"], callback_data=f"be:fac:BBA:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bsc"], callback_data=f"be:fac:BSC:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_fac_baae"], callback_data=f"be:fac:BAAE:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_fac_btech"], callback_data=f"be:fac:BT:{fac}:{ex}"),
    )

    # Exam type filters
    b.add(
        InlineKeyboardButton(text=t["btn_filter_exam_any"], callback_data=f"be:ex:A:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_exam_on"], callback_data=f"be:ex:ON:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_filter_exam_off"], callback_data=f"be:ex:OFF:{fac}:{ex}"),
    )

    # Next step: choose what to edit
    b.add(
        InlineKeyboardButton(text=t["btn_bulk_continue"], callback_data=f"be:fields:{fac}:{ex}"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )

    b.adjust(2)
    return b.as_markup()


def bulk_edit_fields_keyboard(fac: str, ex: str, t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    b.add(InlineKeyboardButton(text=t["btn_set_time"], callback_data=f"be:edit:TIME:{fac}:{ex}"))
    
    if ex != "ON":
        b.add(InlineKeyboardButton(text=t["btn_set_address"], callback_data=f"be:edit:ADDR:{fac}:{ex}"))
        b.add(InlineKeyboardButton(text=t["btn_set_location"], callback_data=f"be:edit:LOC:{fac}:{ex}"))
    
    if ex != "OFF":
        b.add(InlineKeyboardButton(text=t["btn_set_link"], callback_data=f"be:edit:LINK:{fac}:{ex}"))
        b.add(InlineKeyboardButton(text=t["btn_set_login"], callback_data=f"be:edit:LOGIN:{fac}:{ex}"))
        b.add(InlineKeyboardButton(text=t["btn_set_password"], callback_data=f"be:edit:PASS:{fac}:{ex}"))

    b.add(InlineKeyboardButton(text=t["btn_back"], callback_data=f"adm:BULK_EDIT"))

    b.adjust(1)
    return b.as_markup()
