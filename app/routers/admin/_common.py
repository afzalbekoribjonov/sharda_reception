from __future__ import annotations

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.repos.candidates_repo import CandidatesRepo


def cancel_kb(t: dict[str, str]) -> InlineKeyboardMarkup:
    b = InlineKeyboardBuilder()
    b.add(InlineKeyboardButton(text=t["btn_cancel"], callback_data="aa:CANCEL"))
    b.adjust(1)
    return b.as_markup()


def label_fac(code: str) -> str:
    return {"A": "ALL", "BBA": "BBA", "BSC": "BSC", "BAAE": "BAAE", "BT": "B.Tech"}.get(code, "ALL")


def label_ex(code: str) -> str:
    return {"A": "ALL", "ON": "ONLINE", "OFF": "OFFLINE"}.get(code, "ALL")


def label_st(code: str) -> str:
    return {"A": "ALL", "reg": "registered", "draft": "draft"}.get(code, "ALL")


def filters_text(t: dict[str, str], fac: str, ex: str, st: str) -> str:
    return t["admin_filters_title"].format(faculty=label_fac(fac), exam_type=label_ex(ex), status=label_st(st))


def export_text(t: dict[str, str], fac: str, ex: str, st: str, creds: str) -> str:
    creds_label = "ON" if creds == "1" else "OFF"
    return t["export_filters_title"].format(
        faculty=label_fac(fac),
        exam_type=label_ex(ex),
        status=label_st(st),
        creds=creds_label,
    )


def safe_text(doc: dict, key: str, fallback: str) -> str:
    v = doc.get(key)
    if v is None or v == "":
        return fallback
    return str(v)


async def render_user_detail(
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    tid: int,
) -> tuple[str, str | None]:
    doc = await candidates_repo.get_progress(tid) or {}
    name = safe_text(doc, "full_name", "-")
    phone = safe_text(doc, "phone", "-")
    faculty = safe_text(doc, "faculty", "-")
    track = safe_text(doc, "btech_track", "-")
    exam_type = doc.get("exam_type")
    status = safe_text(doc, "status", "-")

    dt = safe_text(doc, "exam_date_time", t["not_set"])
    address = safe_text(doc, "address", t["not_set"])
    link = safe_text(doc, "online_link", t["not_set"])
    login = safe_text(doc, "exam_login", t["not_set"])
    password = safe_text(doc, "exam_password", t["not_set"])
    loc = doc.get("location") or {}
    if isinstance(loc, dict) and loc.get("lat") is not None and loc.get("lng") is not None:
        location = f"{loc['lat']}, {loc['lng']}"
    else:
        location = t["not_set"]

    exam_type_label = str(exam_type or "-")
    if exam_type == "ONLINE":
        text = t["admin_user_detail_online"].format(
            name=name,
            phone=phone,
            faculty=faculty,
            track=track,
            exam_type=exam_type_label,
            status=status,
            dt=dt,
            link=link,
            login=login,
            password=password,
        )
    elif exam_type == "OFFLINE":
        text = t["admin_user_detail_offline"].format(
            name=name,
            phone=phone,
            faculty=faculty,
            track=track,
            exam_type=exam_type_label,
            status=status,
            dt=dt,
            address=address,
            location=location,
        )
    else:
        text = t["admin_user_detail_offline"].format(
            name=name,
            phone=phone,
            faculty=faculty,
            track=track,
            exam_type=exam_type_label,
            status=status,
            dt=dt,
            address=address,
            location=location,
        )
    return text, (str(exam_type) if exam_type else None)
