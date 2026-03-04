# Task 003 — Market hours guard (US equities)

## Goal
Add a simple, deterministic market-hours guard function for **US equities regular trading hours** and tests for it.

## Requirements

### 1) Add function
Create a new module:

- `src/tradingbot/utils/market_hours.py`

Implement:

- `market_hours_guard(now: datetime, calendar_source=None) -> tuple[bool, str]`

Rules:

- Convert `now` to `America/New_York` using `zoneinfo.ZoneInfo`.
- If `now` is **naive** (no tzinfo), treat it as **UTC** (assume UTC, then convert to NY).
- If NY-local weekday is Sat/Sun => `(False, "market closed: weekend")`
- Market open window is:
  - open at **09:30:00**
  - close at **16:00:00**
  - open interval is **[09:30, 16:00)** (16:00 is closed)
- Return reasons:
  - before open: `"market closed: before open"`
  - after close: `"market closed: after close"`
  - open: `"market open"`

No external calendar/holiday logic yet.

### 2) Export from utils package
Update existing:

- `src/tradingbot/utils/__init__.py`

to export:

- `market_hours_guard`

Important: **Preserve existing exports** (do not replace the file content with only this export).

### 3) Tests
Add a new test file:

- `tests/test_market_hours_guard.py`

Test at least:

- Mon 09:29 NY => closed, before open
- Mon 09:30 NY => open
- Mon 15:59:59 NY => open
- Mon 16:00 NY => closed, after close
- Sat noon NY => closed, weekend
- Naive datetime that equals 13:30 UTC on a Monday (i.e., 09:30 NY during EDT) => open

Notes:
- Prefer `datetime.fromisoformat()` with offsets for the NY cases.
- Do NOT modify `tests/test_smoke.py` for this task.

### 4) Non-goals / constraints
- Do NOT modify `src/tradingbot/run.py` for this task.
- Keep style compatible with ruff and the existing repo conventions.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- Function behavior matches rules above
