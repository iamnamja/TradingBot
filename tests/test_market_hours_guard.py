from datetime import datetime
from zoneinfo import ZoneInfo

from tradingbot.utils.market_hours import market_hours_guard


NY = ZoneInfo("America/New_York")


def dt_ny(year, month, day, hour, minute, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=NY)


def test_before_open():
    dt = dt_ny(2023, 8, 7, 9, 29)
    is_open, reason = market_hours_guard(dt)
    assert is_open is False
    assert reason == "market closed: before open"


def test_open_start():
    dt = dt_ny(2023, 8, 7, 9, 30)
    is_open, reason = market_hours_guard(dt)
    assert is_open is True
    assert reason == "market open"


def test_open_end():
    dt = dt_ny(2023, 8, 7, 15, 59, 59)
    is_open, reason = market_hours_guard(dt)
    assert is_open is True
    assert reason == "market open"


def test_after_close():
    dt = dt_ny(2023, 8, 7, 16, 0)
    is_open, reason = market_hours_guard(dt)
    assert is_open is False
    assert reason == "market closed: after close"


def test_weekend():
    dt = dt_ny(2023, 8, 5, 12, 0)
    is_open, reason = market_hours_guard(dt)
    assert is_open is False
    assert reason == "market closed: weekend"


def test_naive_utc():
    # Naive datetime is treated as UTC: 13:30 UTC => 09:30 NY (EDT) => open
    dt = datetime(2023, 8, 7, 13, 30, 0)
    is_open, reason = market_hours_guard(dt)
    assert is_open is True
    assert reason == "market open"
