from __future__ import annotations

from aiogram import Router, F
from aiogram.types import CallbackQuery

from app.db.repos.users_repo import UsersRepo
from app.db.repos.candidates_repo import CandidatesRepo
from app.config import settings
from app.keyboards.menu import (
    main_menu_keyboard,
    settings_keyboard,
    profile_keyboard,
    exam_keyboard,
    sharda_info_keyboard,
)
from app.keyboards.common import lang_keyboard, open_webapp_reply_keyboard
from app.utils.edit import safe_edit_text

router = Router()


def _fmt_dt(value: object) -> str:
    # Hozircha oddiy. Keyin datetime formatini chiroyli qilamiz.
    if value is None:
        return ""
    return str(value)


def _fmt(value: object, fallback: str) -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _label_faculty(code: str | None) -> str:
    mapping = {
        "BBA": "BBA",
        "BSC": "BSC",
        "BAAE": "BAAE",
        "BTECH": "B.Tech",
    }
    return mapping.get(code or "", code or "")


def _label_exam_type(code: str | None) -> str:
    mapping = {"ONLINE": "ONLINE", "OFFLINE": "OFFLINE"}
    return mapping.get(code or "", code or "")


@router.callback_query(F.data == "menu:HOME")
async def menu_home(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["main_menu_title"], reply_markup=main_menu_keyboard(t))


@router.callback_query(F.data == "menu:SETTINGS")
async def menu_settings(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["settings_title"], reply_markup=settings_keyboard(t))


@router.callback_query(F.data == "menu:SHARDA")
async def menu_sharda(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["about_sharda"], reply_markup=sharda_info_keyboard(t))


@router.callback_query(F.data == "sharda:CONTACT")
async def sharda_contact(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["contact_sharda"], reply_markup=sharda_info_keyboard(t))


@router.callback_query(F.data == "sharda:FACULTY")
async def sharda_faculty(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["faculty_info_sharda"], reply_markup=sharda_info_keyboard(t))


@router.callback_query(F.data == "sharda:BACK")
async def sharda_back(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["main_menu_title"], reply_markup=main_menu_keyboard(t))


@router.callback_query(F.data == "menu:EXAM")
async def menu_exam(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
) -> None:
    await callback.answer()

    doc = await candidates_repo.get_progress(callback.from_user.id)

    if not doc or doc.get("status") != "registered":
        await safe_edit_text(callback.message, t["exam_pending"], reply_markup=main_menu_keyboard(t))
        return

    exam_type = doc.get("exam_type")
    exam_dt = doc.get("exam_date_time")
    dt = _fmt_dt(exam_dt) if exam_dt else t["not_set"]

    if exam_type == "OFFLINE":
        address = doc.get("address") or t["not_set"]
        text = t["exam_offline_info"].format(dt=dt, address=address)
        loc = doc.get("location") or {}
        has_location = bool(isinstance(loc, dict) and loc.get("lat") is not None and loc.get("lng") is not None)
        await safe_edit_text(callback.message, text, reply_markup=exam_keyboard(t, has_location))
        return

    if exam_type == "ONLINE":
        link = doc.get("online_link") or t["not_set"]
        login = doc.get("exam_login") or t["not_set"]
        password = doc.get("exam_password") or t["not_set"]
        text = t["exam_online_info"].format(dt=dt, link=link, login=login, password=password)
        await safe_edit_text(callback.message, text, reply_markup=main_menu_keyboard(t))
        return

    await safe_edit_text(callback.message, t["exam_pending"], reply_markup=main_menu_keyboard(t))


@router.callback_query(F.data == "exam:LOC")
async def exam_location(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
) -> None:
    await callback.answer()
    doc = await candidates_repo.get_progress(callback.from_user.id)
    if not doc or doc.get("exam_type") != "OFFLINE":
        return
    loc = doc.get("location") or {}
    if not isinstance(loc, dict):
        return
    lat = loc.get("lat")
    lng = loc.get("lng")
    if lat is None or lng is None:
        return
    url = f"https://www.google.com/maps?q={lat},{lng}"
    await callback.message.answer(t["location_link_text"].format(url=url), disable_web_page_preview=True)
    await callback.message.answer_location(latitude=float(lat), longitude=float(lng))


@router.callback_query(F.data == "menu:PROFILE")
async def menu_profile(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
) -> None:
    await callback.answer()

    doc = await candidates_repo.get_progress(callback.from_user.id)
    not_set = t["not_set"]

    full_name = _fmt((doc or {}).get("full_name"), not_set)
    phone = _fmt((doc or {}).get("phone"), not_set)
    faculty = _label_faculty((doc or {}).get("faculty")) or not_set
    track = _fmt((doc or {}).get("btech_track"), not_set)
    exam_type = _label_exam_type((doc or {}).get("exam_type")) or not_set
    status = _fmt((doc or {}).get("status"), not_set)
    text = t["profile_text"].format(
        name=full_name,
        phone=phone,
        faculty=faculty,
        track=track,
        exam_type=exam_type,
        status=status,
    )

    await safe_edit_text(callback.message, text, reply_markup=profile_keyboard(t))


@router.callback_query(F.data == "profile:EDIT")
async def profile_edit(
    callback: CallbackQuery,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    lang: str,
) -> None:
    doc = await candidates_repo.get_progress(callback.from_user.id)
    exam_dt = (doc or {}).get("exam_date_time")
    if exam_dt:
        await callback.answer(t["profile_edit_blocked"], show_alert=True)
        return

    await callback.answer()
    await safe_edit_text(callback.message, t["profile_edit_prompt"], reply_markup=profile_keyboard(t))
    if settings.WEBAPP_URL:
        await callback.message.answer(
            t["btn_open_webapp"],
            reply_markup=open_webapp_reply_keyboard(t, settings.WEBAPP_URL, lang=lang),
        )


@router.callback_query(F.data == "settings:LANG")
async def settings_lang(callback: CallbackQuery, t: dict[str, str]) -> None:
    await callback.answer()
    await safe_edit_text(callback.message, t["choose_lang"], reply_markup=lang_keyboard(t, back_cb="menu:SETTINGS"))


@router.callback_query(F.data.startswith("setlang:"))
async def set_language_from_settings(
    callback: CallbackQuery,
    users_repo: UsersRepo,
    t: dict[str, str],
) -> None:
    lang = callback.data.split(":", 1)[1].strip()
    await users_repo.set_language(callback.from_user.id, lang)
    await callback.answer("✅")
    await safe_edit_text(callback.message, t["settings_title"], reply_markup=settings_keyboard(t))
