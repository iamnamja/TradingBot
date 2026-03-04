# Task 003: Market Hours Guard

## Goal
Add a small, testable function to determine whether **US equities regular market hours** are open.

## Requirements
1. Create: `src/tradingbot/utils/market_hours.py`
   - Implement: `market_hours_guard(now: datetime, calendar_source=None) -> tuple[bool, str]`
   - Rules:
     - Market timezone: `America/New_York`
     - Open days: Monday–Friday
     - Open window: **09:30:00 <= time < 16:00:00** (16:00 is CLOSED)
     - If `now` is timezone-aware: convert to NY time and evaluate.
     - If `now` is naive: assume it is **UTC**, convert to NY time and evaluate.
   - Return `(True, "market open")` when open.
   - Return `(False, <reason>)` when closed, using EXACT reasons:
     - weekend => `"market closed: weekend"`
     - before open => `"market closed: before open"`
     - after close => `"market closed: after close"`

2. Add tests in: `tests/test_market_hours_guard.py`
   - Test at least:
     - Mon 09:29 NY -> closed (before open)
     - Mon 09:30 NY -> open
     - Mon 15:59:59 NY -> open
     - Mon 16:00 NY -> closed (after close)
     - Sat 12:00 NY -> closed (weekend)
     - Naive UTC datetime that maps to NY 09:30 -> open

3. IMPORTANT: Do NOT modify any existing files besides adding the two new files above.
   - Specifically: **do not edit** `src/tradingbot/utils/__init__.py`, `tests/test_smoke.py`, or `src/tradingbot/run.py`.

## Acceptance
- `ruff check .` passes
- `pytest -q` passes
