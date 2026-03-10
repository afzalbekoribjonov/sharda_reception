from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from aiogram import Bot

from app.db.repos.candidates_repo import CandidatesRepo
from app.db.repos.users_repo import UsersRepo


async def reminder_loop(
    bot: Bot,
    candidates_repo: CandidatesRepo,
    users_repo: UsersRepo,
    translations: dict[str, dict[str, str]],
    tz_name: str,
    interval_seconds: int = 60,
) -> None:
    await candidates_repo.backfill_exam_datetime_utc(tz_name)

    try:
        while True:
            now_utc = datetime.now(timezone.utc)
            try:
                due = await candidates_repo.find_due_reminders(now_utc, minutes=30)
                for doc in due:
                    tid = int(doc.get("telegram_id"))
                    name = str(doc.get("full_name") or "").strip()

                    lang = await users_repo.get_language(tid) or "uz"
                    t = translations.get(lang, translations["uz"])

                    text = t["reminder_30m"].format(name=name)

                    try:
                        await bot.send_message(chat_id=tid, text=text)
                        await candidates_repo.mark_reminder_sent(tid, sent_at=now_utc)
                    except Exception:
                        # keep unsent to retry later
                        pass
                    await asyncio.sleep(0.05)
            except Exception:
                # don't crash the loop
                pass

            await asyncio.sleep(interval_seconds)
    except asyncio.CancelledError:
        return
