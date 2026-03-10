from __future__ import annotations
from aiogram.types import (
    WebAppInfo,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

from app.i18n.loader import SUPPORTED_LANGS


def lang_keyboard(t: dict[str, str], back_cb: str | None = None) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()

    mapping = {
        "uz": t["btn_lang_uz"],
        "ru": t["btn_lang_ru"],
        "en": t["btn_lang_en"],
    }
    for lang in SUPPORTED_LANGS:
        b.add(InlineKeyboardButton(text=mapping[lang], callback_data=f"setlang:{lang}"))

    if back_cb:
        b.add(InlineKeyboardButton(text=t["btn_back"], callback_data=back_cb))
    b.adjust(1)
    return b.as_markup()

def _with_lang(url: str, lang: str | None) -> str:
    if not lang:
        return url
    parsed = urlparse(url)
    q = dict(parse_qsl(parsed.query, keep_blank_values=True))
    q["lang"] = lang.lower()
    return urlunparse(parsed._replace(query=urlencode(q)))


def open_webapp_reply_keyboard(t: dict[str, str], url: str, lang: str | None = None) -> ReplyKeyboardMarkup:
    webapp_url = _with_lang(url, lang)
    b = ReplyKeyboardBuilder()
    b.add(
        KeyboardButton(
            text=t["btn_open_webapp"],
            web_app=WebAppInfo(url=webapp_url),
        )
    )
    b.adjust(1)
    return b.as_markup(resize_keyboard=True, one_time_keyboard=True)
