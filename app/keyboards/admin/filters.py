from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_filters_keyboard(fac: str, ex: str, st: str, t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    b.add(
        InlineKeyboardButton(text=t["btn_filter_fac_any"], callback_data=f"af:fac:A:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bba"], callback_data=f"af:fac:BBA:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bsc"], callback_data=f"af:fac:BSC:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_fac_baae"], callback_data=f"af:fac:BAAE:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_fac_btech"], callback_data=f"af:fac:BT:{fac}:{ex}:{st}"),
    )

    b.add(
        InlineKeyboardButton(text=t["btn_filter_exam_any"], callback_data=f"af:ex:A:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_exam_on"], callback_data=f"af:ex:ON:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_exam_off"], callback_data=f"af:ex:OFF:{fac}:{ex}:{st}"),
    )

    b.add(
        InlineKeyboardButton(text=t["btn_filter_status_any"], callback_data=f"af:st:A:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_status_reg"], callback_data=f"af:st:reg:{fac}:{ex}:{st}"),
        InlineKeyboardButton(text=t["btn_filter_status_draft"], callback_data=f"af:st:draft:{fac}:{ex}:{st}"),
    )

    b.add(
        InlineKeyboardButton(text=t["btn_show_list"], callback_data=f"au:l:{fac}:{ex}:{st}:0"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )

    b.adjust(2)
    return b.as_markup()


# ---------------- Excel export ----------------

def export_filters_keyboard(fac: str, ex: str, st: str, creds: str, t: dict[str, str]) -> InlineKeyboardMarkup:
    """
    fac: A|BBA|BSC|BAAE|BT
    ex:  A|ON|OFF
    st:  A|reg|draft
    creds: 0|1
    """
    b = InlineKeyboardBuilder()

    b.add(
        InlineKeyboardButton(text=t["btn_filter_fac_any"], callback_data=f"exf:fac:A:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bba"], callback_data=f"exf:fac:BBA:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_fac_bsc"], callback_data=f"exf:fac:BSC:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_fac_baae"], callback_data=f"exf:fac:BAAE:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_fac_btech"], callback_data=f"exf:fac:BT:{fac}:{ex}:{st}:{creds}"),
    )

    b.add(
        InlineKeyboardButton(text=t["btn_filter_exam_any"], callback_data=f"exf:ex:A:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_exam_on"], callback_data=f"exf:ex:ON:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_exam_off"], callback_data=f"exf:ex:OFF:{fac}:{ex}:{st}:{creds}"),
    )

    b.add(
        InlineKeyboardButton(text=t["btn_filter_status_any"], callback_data=f"exf:st:A:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_status_reg"], callback_data=f"exf:st:reg:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_filter_status_draft"], callback_data=f"exf:st:draft:{fac}:{ex}:{st}:{creds}"),
    )

    creds_btn = t["btn_creds_on"] if creds == "1" else t["btn_creds_off"]
    b.add(
        InlineKeyboardButton(text=creds_btn, callback_data=f"exf:creds:T:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_generate_excel"], callback_data=f"exg:{fac}:{ex}:{st}:{creds}"),
        InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"),
    )

    b.adjust(2)
    return b.as_markup()
