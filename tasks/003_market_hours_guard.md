# Task 003 — Market Hours Guard (US Equities RTH)

## Goal
Introduce a reusable `market_hours_guard` helper for **US equities regular trading hours (RTH)** and add tests.

## IMPORTANT: Idempotency / No-op
Before making ANY changes:
1) Inspect the repo state.
2) If `src/tradingbot/utils/market_hours.py` already exists, tests exist, and `ruff check .` + `pytest -q` are green, **DO NOT CHANGE ANY FILES**.
Return an explicit note: **NO_CHANGES_NEEDED** and produce **no diff**.

## Requirements
### 1) New module
Create:
- `src/tradingbot/utils/market_hours.py`

It must implement:
```py
def market_hours_guard(now: datetime, calendar_source: object | None = None) -> tuple[bool, str]:
    ...
```
Rules:
- If `now` is naive, treat it as **UTC** first, then convert to **America/New_York**
- Weekend => `(False, "market closed: weekend")`
- Weekday time window (NY local time):
  - before 09:30 => `(False, "market closed: before open")`
  - 09:30 <= t < 16:00 => `(True, "market open")`
  - at/after 16:00 => `(False, "market closed: after close")`
- Ignore holidays for now (`calendar_source` unused).

### 2) Package export (ruff-safe)
If you re-export from `src/tradingbot/utils/__init__.py`, it MUST be ruff-safe:
- Use `# noqa: F401` on the import line, AND
- Define `__all__ = ["market_hours_guard"]`

Example:
```py
from .market_hours import market_hours_guard  # noqa: F401
__all__ = ["market_hours_guard"]
```

If the repo already prefers importing from `tradingbot.utils.market_hours`, you may skip re-export.

### 3) Tests
Create:
- `tests/test_market_hours_guard.py`

Tests must cover at least:
- Before open (Mon 09:29 NY) => closed: before open
- Open at open (Mon 09:30 NY) => market open
- Open near close (Mon 15:59:59 NY) => market open
- After close (Mon 16:00 NY) => closed: after close
- Weekend (Sat noon NY) => closed: weekend
- Naive UTC (Mon 13:30 naive) => 09:30 NY => market open

**Do not import pytest unless you actually use it** (ruff F401). Plain asserts are fine.

### 4) CI
After changes:
- `ruff check .` must be green
- `pytest -q` must be green
- No unused imports.
- No placeholder comments like “# empty???”

## Files you MAY touch
- `src/tradingbot/utils/market_hours.py` (new)
- `src/tradingbot/utils/__init__.py` (optional, only if needed)
- `tests/test_market_hours_guard.py` (new)
- `tests/conftest.py` (only if needed for import path; prefer not touching if already works)

Return a clean diff only.
