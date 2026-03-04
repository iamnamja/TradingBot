# Task 003: Market hours guard (US equities RTH)

## Goal
Implement a reusable **market-hours guard** for US equities regular trading hours, with unit tests.

This bot is long-only for now and runs on a schedule. We want a small utility that answers:
- is the market open right now?
- if not, why?

## Requirements

### Implementation
1) Create: `src/tradingbot/utils/market_hours.py`
   - Export function:
     - `market_hours_guard(now: datetime, calendar_source: object | None = None) -> tuple[bool, str]`
   - Rules:
     - Use America/New_York
     - Weekend (Sat/Sun) => closed: `"market closed: weekend"`
     - Before 09:30 NY => closed: `"market closed: before open"`
     - At/after 16:00 NY => closed: `"market closed: after close"`
     - Otherwise open: `"market open"`
   - Input handling:
     - If `now` is naive: treat as **UTC**, then convert to NY
     - If `now` is tz-aware: convert to NY

2) Update: `src/tradingbot/utils/__init__.py`
   - Ensure `market_hours_guard` is importable from `tradingbot.utils`
   - IMPORTANT: Do not assume this file is empty.
     - If it already contains exports, keep them and add the new import.

3) (Optional but preferred) Update: `src/tradingbot/run.py`
   - If `run.py` contains an inline `market_hours_guard`, remove it and import:
     - `from tradingbot.utils.market_hours import market_hours_guard`
   - Keep existing runtime behavior the same.

### Tests
4) Add: `tests/test_market_hours_guard.py`
   - Must NOT require network calls.
   - Cases to cover:
     - Mon 09:29 NY => closed (before open)
     - Mon 09:30 NY => open
     - Mon 15:59:59 NY => open
     - Mon 16:00 NY => closed (after close)
     - Sat noon NY => closed (weekend)
     - Naive `2023-08-07 13:30:00` (UTC) => open (09:30 NY)

5) Do NOT modify `tests/test_smoke.py` unless required to fix imports.

## Acceptance Criteria
- `ruff check .` passes
- `pytest -q` passes
- Function is importable via:
  - `from tradingbot.utils.market_hours import market_hours_guard`
  - `from tradingbot.utils import market_hours_guard`

## Notes
- Do not add holiday calendars yet (we’ll extend later).
