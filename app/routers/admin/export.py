from __future__ import annotations

from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.types import CallbackQuery
from aiogram.types.input_file import FSInputFile

from app.db.repos.candidates_repo import CandidatesRepo
from app.keyboards.admin import export_filters_keyboard
from app.routers.admin._common import export_text
from app.services.excel_export import build_candidates_excel
from app.utils.edit import safe_edit_text

router = Router()


@router.callback_query(F.data.startswith("exf:"))
async def export_filters_update(callback: CallbackQuery, t: dict[str, str], is_admin: bool) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    _, field, value, fac, ex, st, creds = callback.data.split(":", 6)

    if field == "fac":
        fac = value
    elif field == "ex":
        ex = value
    elif field == "st":
        st = value
    elif field == "creds":
        creds = "0" if creds == "1" else "1"

    await callback.answer()
    await safe_edit_text(
        callback.message,
        export_text(t, fac, ex, st, creds),
        reply_markup=export_filters_keyboard(fac, ex, st, creds, t),
    )


@router.callback_query(F.data.startswith("exg:"))
async def export_generate(
    callback: CallbackQuery,
    bot: Bot,
    candidates_repo: CandidatesRepo,
    t: dict[str, str],
    is_admin: bool,
) -> None:
    if not is_admin:
        await callback.answer(t["admin_only"], show_alert=True)
        return

    _, fac, ex, st, creds = callback.data.split(":", 4)
    include_creds = creds == "1"

    await callback.answer()
    await safe_edit_text(callback.message, t["export_generating"], reply_markup=None)

    rows = await candidates_repo.export_rows(fac, ex, st)
    if not rows:
        await safe_edit_text(
            callback.message,
            t["export_no_data"],
            reply_markup=export_filters_keyboard(fac, ex, st, creds, t),
        )
        return

    out_path = build_candidates_excel(rows, include_credentials=include_creds, out_dir=Path("tmp_exports"))
    doc = FSInputFile(str(out_path), filename=out_path.name)

    await bot.send_document(chat_id=callback.message.chat.id, document=doc, caption=t["export_sent"])
    await safe_edit_text(
        callback.message,
        export_text(t, fac, ex, st, creds),
        reply_markup=export_filters_keyboard(fac, ex, st, creds, t),
    )
