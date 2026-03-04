from datetime import datetime
from zoneinfo import ZoneInfo

from tradingbot.utils.market_hours import market_hours_guard


NY = ZoneInfo("America/New_York")


def dt_ny(y, m, d, hh, mm, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=NY)


def test_before_open():
    is_open, reason = market_hours_guard(dt_ny(2023, 8, 7, 9, 29))
    assert is_open is False
    assert reason == "market closed: before open"


def test_open_start():
    is_open, reason = market_hours_guard(dt_ny(2023, 8, 7, 9, 30))
    assert is_open is True
    assert reason == "market open"


def test_open_end():
    is_open, reason = market_hours_guard(dt_ny(2023, 8, 7, 15, 59, 59))
    assert is_open is True
    assert reason == "market open"


def test_after_close():
    is_open, reason = market_hours_guard(dt_ny(2023, 8, 7, 16, 0))
    assert is_open is False
    assert reason == "market closed: after close"


def test_weekend():
    is_open, reason = market_hours_guard(dt_ny(2023, 8, 5, 12, 0))
    assert is_open is False
    assert reason == "market closed: weekend"


def test_naive_utc_is_treated_as_utc():
    naive = datetime(2023, 8, 7, 13, 30, 0)  # 13:30 UTC == 09:30 NY (EDT)
    is_open, reason = market_hours_guard(naive)
    assert is_open is True
    assert reason == "market open"
