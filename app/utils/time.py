from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

EXAM_DT_FORMAT = "%Y-%m-%d %H:%M"


def parse_exam_datetime(value: str, tz_name: str) -> datetime:
    text = (value or "").strip()
    dt_naive = datetime.strptime(text, EXAM_DT_FORMAT)
    tz = ZoneInfo(tz_name)
    dt_local = dt_naive.replace(tzinfo=tz)
    return dt_local.astimezone(timezone.utc)
