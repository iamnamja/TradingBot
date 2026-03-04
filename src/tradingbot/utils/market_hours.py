from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo


def market_hours_guard(
    now: datetime, calendar_source: object | None = None
) -> tuple[bool, str]:
    """Return whether US equities market is open during regular trading hours.

    Rules (no holiday calendar yet):
      - Mon–Fri only
      - 09:30 <= local NY time < 16:00

    Args:
        now: timezone-aware datetime; if naive, it is treated as UTC.
        calendar_source: unused placeholder for future holiday calendar support.

    Returns:
        (is_open, reason)
        - If open: (True, "market open")
        - If closed: (False, one of)
            "market closed: weekend"
            "market closed: before open"
            "market closed: after close"
    """
    ny_tz = ZoneInfo("America/New_York")

    if now.tzinfo is None:
        # Naive datetimes are treated as UTC (explicit and deterministic).
        now = now.replace(tzinfo=ZoneInfo("UTC"))

    now_ny = now.astimezone(ny_tz)

    if now_ny.weekday() >= 5:
        return False, "market closed: weekend"

    open_time = time(9, 30)
    close_time = time(16, 0)
    current_time = now_ny.time()

    if current_time < open_time:
        return False, "market closed: before open"
    if current_time >= close_time:
        return False, "market closed: after close"

    return True, "market open"
