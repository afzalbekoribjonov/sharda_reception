from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def admin_list_keyboard(
    items: list[tuple[int, str, str]],
    fac: str,
    ex: str,
    st: str,
    page: int,
    pages: int,
    t: dict[str, str],
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    for tid, name, phone in items:
        text = f"{name} — {phone}"
        b.add(InlineKeyboardButton(text=text[:60], callback_data=f"au:v:{tid}:{fac}:{ex}:{st}:{page}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t["btn_prev"], callback_data=f"au:l:{fac}:{ex}:{st}:{page - 1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text=t["btn_next"], callback_data=f"au:l:{fac}:{ex}:{st}:{page + 1}"))

    for x in nav:
        b.add(x)

    b.add(InlineKeyboardButton(text=t["btn_back_filters"], callback_data=f"adm:FILT:{fac}:{ex}:{st}"))

    b.adjust(1)
    return b.as_markup()


def admin_pending_list_keyboard(
    items: list[tuple[int, str, str]],
    kind: str,
    page: int,
    pages: int,
    t: dict[str, str],
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    for tid, name, phone in items:
        text = f"{name} — {phone}"
        b.add(InlineKeyboardButton(text=text[:60], callback_data=f"ap:V:{tid}:{kind}:{page}"))

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text=t["btn_prev"], callback_data=f"ap:K:{kind}:{page - 1}"))
    if page < pages - 1:
        nav.append(InlineKeyboardButton(text=t["btn_next"], callback_data=f"ap:K:{kind}:{page + 1}"))

    for x in nav:
        b.add(x)

    b.add(InlineKeyboardButton(text=t["btn_back_filters"], callback_data="adm:PENDING"))

    b.adjust(1)
    return b.as_markup()


def admin_user_detail_keyboard(
    tid: int,
    return_kind: str,
    return_page: int,
    t: dict[str, str],
    exam_type: str | None,
    return_fac: str | None = None,
    return_ex: str | None = None,
    return_st: str | None = None,
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    extra = ""
    if return_kind == "LIST" and return_fac and return_ex and return_st:
        extra = f":{return_fac}:{return_ex}:{return_st}"

    et = (exam_type or "").upper()
    allow_addr = et != "ONLINE"
    allow_online = et != "OFFLINE"

    b.add(InlineKeyboardButton(text=t["btn_set_time"], callback_data=f"ae:TIME:{tid}:{return_kind}:{return_page}{extra}"))
    if allow_addr:
        b.add(InlineKeyboardButton(text=t["btn_set_address"], callback_data=f"ae:ADDR:{tid}:{return_kind}:{return_page}{extra}"))
        b.add(InlineKeyboardButton(text=t["btn_set_location"], callback_data=f"ae:LOC:{tid}:{return_kind}:{return_page}{extra}"))
    if allow_online:
        b.add(InlineKeyboardButton(text=t["btn_set_link"], callback_data=f"ae:LINK:{tid}:{return_kind}:{return_page}{extra}"))
        b.add(InlineKeyboardButton(text=t["btn_set_login"], callback_data=f"ae:LOGIN:{tid}:{return_kind}:{return_page}{extra}"))
        b.add(InlineKeyboardButton(text=t["btn_set_password"], callback_data=f"ae:PASS:{tid}:{return_kind}:{return_page}{extra}"))

    if return_kind == "LIST":
        if return_fac and return_ex and return_st:
            b.add(
                InlineKeyboardButton(
                    text=t["btn_back_list"],
                    callback_data=f"au:l:{return_fac}:{return_ex}:{return_st}:{return_page}",
                )
            )
        else:
            b.add(InlineKeyboardButton(text=t["btn_back_list"], callback_data="adm:USERS"))
    else:
        b.add(InlineKeyboardButton(text=t["btn_back_list"], callback_data=f"ap:K:{return_kind}:{return_page}"))

    b.adjust(2)
    return b.as_markup()


def admins_list_keyboard(
    items: list[tuple[int, str]],
    page: int,
    pages: int,
    t: dict[str, str],
) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    for tid, role in items:
        label = f"{tid} — {role}"
        b.add(InlineKeyboardButton(text=label[:40], callback_data="sa:noop"))

        if role == "super":
            b.add(InlineKeyboardButton(text="—", callback_data="sa:noop"))
        else:
            b.add(InlineKeyboardButton(text=t["btn_remove_admin"], callback_data=f"sa:rm:{tid}:{page}"))

    if pages > 1:
        if page > 0:
            b.add(InlineKeyboardButton(text=t["btn_prev"], callback_data=f"sa:l:{page - 1}"))
        if page < pages - 1:
            b.add(InlineKeyboardButton(text=t["btn_next"], callback_data=f"sa:l:{page + 1}"))

    b.add(InlineKeyboardButton(text=t["btn_admin_back"], callback_data="adm:HOME"))
    b.adjust(2)
    return b.as_markup()
