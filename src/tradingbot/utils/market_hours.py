from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def market_hours_guard(now: datetime, calendar_source: object | None = None) -> tuple[bool, str]:
    """Return whether US equities market is open (RTH) for a given datetime.

    Rules (no holidays yet):
    - Mon–Fri only
    - 09:30 <= time < 16:00 in America/New_York
    - If `now` is naive, treat it as UTC first, then convert to NY.
    """
    _ = calendar_source  # reserved for future use

    ny_tz = ZoneInfo("America/New_York")

    if now.tzinfo is None:
        now = now.replace(tzinfo=ZoneInfo("UTC"))

    now_ny = now.astimezone(ny_tz)

    if now_ny.weekday() >= 5:
        return False, "market closed: weekend"

    open_time = time(9, 30, 0)
    close_time = time(16, 0, 0)
    t = now_ny.time()

    if t < open_time:
        return False, "market closed: before open"
    if t >= close_time:
        return False, "market closed: after close"

    return True, "market open"
