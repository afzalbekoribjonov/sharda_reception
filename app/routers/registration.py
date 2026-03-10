from __future__ import annotations

import json

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove

from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo
from app.keyboards.faculty import faculty_keyboard, btech_tracks_keyboard
from app.keyboards.exam_type import exam_type_keyboard
from app.keyboards.menu import main_menu_keyboard
from app.utils.edit import safe_edit_text
from app.utils.why_choose import maybe_send_why_choose_sharda

router = Router()


def _normalize_phone(phone: str) -> str:
    return phone.strip().replace(" ", "")

def _faculty_label(code: str, t: dict[str, str]) -> str:
    return {
        "BBA": t["faculty_bba"],
        "BSC": t["faculty_bsc"],
        "BAAE": t["faculty_baae"],
        "BTECH": t["faculty_btech"],
    }.get(code or "", code or "-")


async def _remove_reply_keyboard(message: Message) -> None:
    tmp = await message.answer(".", reply_markup=ReplyKeyboardRemove())
    try:
        await tmp.delete()
    except Exception:
        pass


@router.message(F.web_app_data)
async def on_webapp_data(
    message: Message,
    users_repo: UsersRepo,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    lang: str,
) -> None:
    # agar registered bo'lsa qayta ro'yxatdan o'tkazmaymiz
    status = await candidates_repo.get_status(message.from_user.id)
    if status == "registered":
        doc = await candidates_repo.get_progress(message.from_user.id)
        exam_dt = (doc or {}).get("exam_date_time")
        if exam_dt:
            await _remove_reply_keyboard(message)
            await message.answer(t["profile_edit_blocked"], reply_markup=main_menu_keyboard(t))
            return
        # exam date not set: allow user to re-submit data

    try:
        payload = json.loads(message.web_app_data.data)
    except Exception:
        await message.answer("WebApp data error.")
        return

    full_name = str(payload.get("full_name", "")).strip()
    phone = _normalize_phone(str(payload.get("phone", "")))

    if len(full_name) < 3:
        await message.answer("full_name is too short.")
        return
    if len(phone) < 7:
        await message.answer("phone is invalid.")
        return

    existing = await candidates_repo.find_registered_by_phone(phone)
    if existing and int(existing.get("telegram_id") or 0) != message.from_user.id:
        name = str(existing.get("full_name") or "-")
        faculty = _faculty_label(str(existing.get("faculty") or ""), t)
        await message.answer(
            t["phone_already_registered"].format(
                name=name,
                faculty=faculty,
                user=full_name,
            )
        )
        return

    await users_repo.ensure_user(message.from_user.id)
    await candidates_repo.upsert_draft(
        telegram_id=message.from_user.id,
        full_name=full_name,
        phone=phone,
        language=lang,
    )

    await _remove_reply_keyboard(message)
    await message.answer(
        t["choose_faculty"],
        reply_markup=faculty_keyboard(t),
    )


@router.callback_query(F.data.startswith("faculty:"))
async def on_faculty(callback: CallbackQuery, candidates_repo: CandidatesRepo, t: dict[str, str]) -> None:
    faculty = callback.data.split(":", 1)[1]

    if faculty not in {"BBA", "BSC", "BAAE", "BTECH"}:
        await callback.answer("Invalid", show_alert=True)
        return

    await candidates_repo.set_faculty(callback.from_user.id, faculty)
    await callback.answer("✅")

    if faculty == "BTECH":
        await safe_edit_text(callback.message, t["choose_btech_track"], reply_markup=btech_tracks_keyboard(t))
    else:
        await safe_edit_text(callback.message, t["choose_exam_type"], reply_markup=exam_type_keyboard(t))


@router.callback_query(F.data.startswith("btech:"))
async def on_btech_track(callback: CallbackQuery, candidates_repo: CandidatesRepo, t: dict[str, str]) -> None:
    action = callback.data.split(":", 1)[1]

    if action == "BACK":
        await callback.answer()
        await safe_edit_text(callback.message, t["choose_faculty"], reply_markup=faculty_keyboard(t))
        return

    if action not in {"CSE", "AIML", "CYBER"}:
        await callback.answer("Invalid", show_alert=True)
        return

    await candidates_repo.set_btech_track(callback.from_user.id, action)
    await callback.answer("✅")

    await safe_edit_text(callback.message, t["choose_exam_type"], reply_markup=exam_type_keyboard(t))


@router.callback_query(F.data.in_({"exam:ONLINE", "exam:OFFLINE"}))
async def on_exam_type(callback: CallbackQuery, candidates_repo: CandidatesRepo, t: dict[str, str]) -> None:
    exam_type = callback.data.split(":", 1)[1]

    await candidates_repo.set_exam_type(callback.from_user.id, exam_type)
    await callback.answer("✅")

    # Endi registered bo'ldi -> info post, keyin menyu
    await safe_edit_text(
        callback.message,
        t["registered_done"],
        reply_markup=None,
    )
    await maybe_send_why_choose_sharda(callback.message, candidates_repo, t, allow_repeat=True)
    await callback.message.answer(t["main_menu_title"], reply_markup=main_menu_keyboard(t))




