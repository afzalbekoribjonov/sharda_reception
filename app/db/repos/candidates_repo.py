from __future__ import annotations

import re
from datetime import datetime, timezone, timedelta
from typing import Any

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.utils.time import parse_exam_datetime

_PROGRESS_FIELDS: dict[str, int] = {
    "status": 1,
    "full_name": 1,
    "phone": 1,
    "faculty": 1,
    "btech_track": 1,
    "exam_type": 1,
    "exam_date_time": 1,
    "address": 1,
    "location": 1,
    "online_link": 1,
    "exam_login": 1,
    "exam_password": 1,
    "why_choose_sharda_sent": 1,
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _missing(field: str) -> list[dict[str, Any]]:
    return [{field: {"$exists": False}}, {field: None}, {field: ""}]


class CandidatesRepo:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.col = db["candidates"]

    async def _update(
        self,
        telegram_id: int,
        set_fields: dict[str, Any],
        *,
        upsert: bool = True,
        set_on_insert: dict[str, Any] | None = None,
        now: datetime | None = None,
    ) -> None:
        ts = now or _now()
        update: dict[str, Any] = {"$set": {**set_fields, "updated_at": ts}}
        if set_on_insert:
            update["$setOnInsert"] = set_on_insert
        await self.col.update_one({"telegram_id": telegram_id}, update, upsert=upsert)

    async def _update_admin(self, telegram_id: int, set_fields: dict[str, Any], admin_id: int) -> None:
        await self._update(telegram_id, {**set_fields, "updated_by_admin_id": admin_id})

    async def upsert_draft(self, telegram_id: int, full_name: str, phone: str, language: str) -> None:
        now = _now()
        await self._update(
            telegram_id,
            {
                "telegram_id": telegram_id,
                "full_name": full_name,
                "phone": phone,
                "language": language,
                "status": "draft",
            },
            set_on_insert={"created_at": now},
            now=now,
        )

    async def set_faculty(self, telegram_id: int, faculty: str) -> None:
        await self._update(telegram_id, {"faculty": faculty, "btech_track": None})

    async def set_btech_track(self, telegram_id: int, track: str) -> None:
        await self._update(telegram_id, {"btech_track": track})

    async def set_exam_type(self, telegram_id: int, exam_type: str) -> None:
        await self._update(telegram_id, {"exam_type": exam_type, "status": "registered"})

    async def get_by_telegram_id(self, telegram_id: int) -> dict[str, Any] | None:
        return await self.col.find_one({"telegram_id": telegram_id})

    async def get_status(self, telegram_id: int) -> str | None:
        doc = await self.col.find_one({"telegram_id": telegram_id}, {"status": 1})
        if not doc:
            return None
        return doc.get("status")

    async def get_progress(self, telegram_id: int) -> dict[str, Any] | None:
        return await self.col.find_one({"telegram_id": telegram_id}, _PROGRESS_FIELDS)

    # -------- Admin list helpers --------

    def _build_admin_filter_query(self, fac: str, ex: str, st: str) -> dict[str, Any]:
        q: dict[str, Any] = {}

        if fac != "A":
            q["faculty"] = "BTECH" if fac == "BT" else fac

        if ex != "A":
            q["exam_type"] = "ONLINE" if ex == "ON" else "OFFLINE"

        if st != "A":
            q["status"] = "registered" if st == "reg" else "draft"

        return q

    async def admin_count(self, fac: str, ex: str, st: str) -> int:
        q = self._build_admin_filter_query(fac, ex, st)
        return int(await self.col.count_documents(q))

    async def admin_list_page(self, fac: str, ex: str, st: str, page: int, page_size: int = 10) -> list[dict[str, Any]]:
        q = self._build_admin_filter_query(fac, ex, st)
        cur = (
            self.col.find(q, {"telegram_id": 1, "full_name": 1, "phone": 1})
            .sort("updated_at", -1)
            .skip(page * page_size)
            .limit(page_size)
        )
        return await cur.to_list(length=page_size)

    # -------- Admin edit setters --------

    async def set_exam_datetime(self, telegram_id: int, dt_text: str, dt_utc: datetime, admin_id: int) -> None:
        await self._update_admin(
            telegram_id,
            {
                "exam_date_time": dt_text,
                "exam_datetime_utc": dt_utc,
                "reminder_30m_sent": False,
                "reminder_30m_sent_at": None,
            },
            admin_id,
        )

    async def set_offline_address(self, telegram_id: int, address: str, admin_id: int) -> None:
        await self._update_admin(telegram_id, {"address": address}, admin_id)

    async def set_offline_location(self, telegram_id: int, lat: float, lng: float, admin_id: int) -> None:
        await self._update_admin(telegram_id, {"location": {"lat": lat, "lng": lng}}, admin_id)

    async def set_online_link(self, telegram_id: int, link: str, admin_id: int) -> None:
        await self._update_admin(telegram_id, {"online_link": link}, admin_id)

    async def set_online_login(self, telegram_id: int, login: str, admin_id: int) -> None:
        await self._update_admin(telegram_id, {"exam_login": login}, admin_id)

    async def set_online_password(self, telegram_id: int, password: str, admin_id: int) -> None:
        await self._update_admin(telegram_id, {"exam_password": password}, admin_id)

    # -------- Pending queries --------

    def _q_missing_time(self) -> dict[str, Any]:
        return {"status": "registered", "$or": _missing("exam_date_time")}

    def _q_missing_creds(self) -> dict[str, Any]:
        return {
            "status": "registered",
            "exam_type": "ONLINE",
            "$or": _missing("online_link") + _missing("exam_login") + _missing("exam_password"),
        }

    def _q_missing_addr(self) -> dict[str, Any]:
        return {"status": "registered", "exam_type": "OFFLINE", "$or": _missing("address")}

    def _pending_query(self, kind: str) -> dict[str, Any]:
        if kind == "TIME":
            return self._q_missing_time()
        if kind == "CREDS":
            return self._q_missing_creds()
        if kind == "ADDR":
            return self._q_missing_addr()
        return {
            "status": "registered",
            "$or": [
                {"$or": self._q_missing_time()["$or"]},
                {"exam_type": "ONLINE", "$or": self._q_missing_creds()["$or"]},
                {"exam_type": "OFFLINE", "$or": self._q_missing_addr()["$or"]},
            ],
        }

    async def pending_count(self, kind: str) -> int:
        q = self._pending_query(kind)
        return int(await self.col.count_documents(q))

    async def pending_list_page(self, kind: str, page: int, page_size: int = 10) -> list[dict[str, Any]]:
        q = self._pending_query(kind)
        cur = (
            self.col.find(q, {"telegram_id": 1, "full_name": 1, "phone": 1})
            .sort("updated_at", -1)
            .skip(page * page_size)
            .limit(page_size)
        )
        return await cur.to_list(length=page_size)

    # -------- Export --------

    async def export_rows(self, fac: str, ex: str, st: str, limit: int = 20000) -> list[dict[str, Any]]:
        """
        Returns rows for Excel export. Sorted by updated_at desc.
        """
        q = self._build_admin_filter_query(fac, ex, st)
        proj = {
            "telegram_id": 1,
            "full_name": 1,
            "phone": 1,
            "faculty": 1,
            "btech_track": 1,
            "exam_type": 1,
            "exam_date_time": 1,
            "address": 1,
            "location": 1,
            "online_link": 1,
            "exam_login": 1,
            "exam_password": 1,
            "status": 1,
            "updated_at": 1,
        }
        cur = self.col.find(q, proj).sort("updated_at", -1).limit(limit)
        return await cur.to_list(length=limit)

    async def stats(self) -> dict[str, int]:
        """
        Stats for registered users + pending counters.
        """
        total = int(await self.col.count_documents({"status": "registered"}))

        bba = int(await self.col.count_documents({"status": "registered", "faculty": "BBA"}))
        bsc = int(await self.col.count_documents({"status": "registered", "faculty": "BSC"}))
        baae = int(await self.col.count_documents({"status": "registered", "faculty": "BAAE"}))
        btech = int(await self.col.count_documents({"status": "registered", "faculty": "BTECH"}))

        online = int(await self.col.count_documents({"status": "registered", "exam_type": "ONLINE"}))
        offline = int(await self.col.count_documents({"status": "registered", "exam_type": "OFFLINE"}))

        p_time = await self.pending_count("TIME")
        p_creds = await self.pending_count("CREDS")
        p_addr = await self.pending_count("ADDR")
        p_all = await self.pending_count("ALL")

        return {
            "total": total,
            "bba": bba,
            "bsc": bsc,
            "baae": baae,
            "btech": btech,
            "online": online,
            "offline": offline,
            "p_time": int(p_time),
            "p_creds": int(p_creds),
            "p_addr": int(p_addr),
            "p_all": int(p_all),
        }

    def _q_ready(self) -> dict[str, Any]:
        return {
            "status": "registered",
            "exam_date_time": {"$exists": True, "$nin": ["", None]},
            "$or": [
                {
                    "exam_type": "ONLINE",
                    "online_link": {"$exists": True, "$nin": ["", None]},
                    "exam_login": {"$exists": True, "$nin": ["", None]},
                    "exam_password": {"$exists": True, "$nin": ["", None]},
                },
                {
                    "exam_type": "OFFLINE",
                    "address": {"$exists": True, "$nin": ["", None]},
                },
            ],
        }

    def _q_pending_any(self) -> dict[str, Any]:
        return self._pending_query("ALL")

    def _q_target(self, kind: str) -> dict[str, Any]:
        if kind == "OFF":
            return {"exam_type": "OFFLINE"}
        if kind == "ON":
            return {"exam_type": "ONLINE"}
        if kind == "READY":
            return self._q_ready()
        if kind == "PENDING":
            return self._q_pending_any()
        return {}

    async def target_count(self, kind: str) -> int:
        q = self._q_target(kind)
        return int(await self.col.count_documents(q))

    async def target_tids(self, kind: str) -> list[int]:
        q = self._q_target(kind)
        cur = self.col.find(q, {"telegram_id": 1})
        docs = await cur.to_list(length=200000)
        return [int(d["telegram_id"]) for d in docs if d.get("telegram_id")]

    async def all_tids(self) -> list[int]:
        return await self.target_tids("ALL")

    async def find_by_phone(self, phone: str) -> dict[str, Any] | None:
        digits = re.sub(r"\D+", "", phone or "")
        if len(digits) >= 9:
            digits = digits[-9:]

        q = {"phone": {"$regex": f"{digits}$"}} if digits else {"phone": phone}
        return await self.col.find_one(q, {"telegram_id": 1, "full_name": 1, "phone": 1})

    async def find_registered_by_phone(self, phone: str) -> dict[str, Any] | None:
        digits = re.sub(r"\D+", "", phone or "")
        if len(digits) >= 9:
            digits = digits[-9:]

        q = {"status": "registered", "phone": {"$regex": f"{digits}$"}} if digits else {"status": "registered", "phone": phone}
        return await self.col.find_one(q, {"telegram_id": 1, "full_name": 1, "phone": 1, "faculty": 1})

    # -------- One-time post --------

    async def is_why_choose_sharda_sent(self, telegram_id: int) -> bool:
        doc = await self.col.find_one(
            {"telegram_id": telegram_id},
            {"why_choose_sharda_sent": 1},
        )
        return bool(doc and doc.get("why_choose_sharda_sent"))

    async def mark_why_choose_sharda_sent(self, telegram_id: int) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {"$set": {"why_choose_sharda_sent": True}},
            upsert=True,
        )

    # -------- Reminders --------

    async def find_due_reminders(self, now_utc: datetime, minutes: int = 30) -> list[dict[str, Any]]:
        upper = now_utc + timedelta(minutes=minutes)
        q = {
            "status": "registered",
            "exam_datetime_utc": {"$exists": True, "$gte": now_utc, "$lte": upper},
            "$or": [{"reminder_30m_sent": {"$exists": False}}, {"reminder_30m_sent": False}],
        }
        cur = self.col.find(q, {"telegram_id": 1, "full_name": 1})
        return await cur.to_list(length=10000)

    async def mark_reminder_sent(self, telegram_id: int, sent_at: datetime | None = None) -> None:
        await self.col.update_one(
            {"telegram_id": telegram_id},
            {
                "$set": {
                    "reminder_30m_sent": True,
                    "reminder_30m_sent_at": sent_at or _now(),
                }
            },
        )

    async def backfill_exam_datetime_utc(self, tz_name: str) -> int:
        q = {
            "exam_date_time": {"$exists": True, "$nin": ["", None]},
            "exam_datetime_utc": {"$exists": False},
        }
        cur = self.col.find(q, {"telegram_id": 1, "exam_date_time": 1})
        updated = 0
        async for doc in cur:
            dt_text = str(doc.get("exam_date_time") or "").strip()
            if not dt_text:
                continue
            try:
                dt_utc = parse_exam_datetime(dt_text, tz_name)
            except Exception:
                continue
            await self.col.update_one(
                {"telegram_id": doc["telegram_id"]},
                {"$set": {"exam_datetime_utc": dt_utc}},
            )
            updated += 1
        return updated
