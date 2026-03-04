# Task 003: Market hours guard (US equities, minimal + testable)

Goal: add a reusable guard that determines whether US equities market is open.

Requirements:
- Implement a function:
    market_hours_guard(now: datetime, calendar_source=None) -> tuple[bool, str]
- Rules (simple for now):
  - Monday–Friday only
  - 09:30 <= time < 16:00 America/New_York
  - If closed, return False with a short reason string:
      "market closed: weekend"
      "market closed: before open"
      "market closed: after close"
- Handle timezone properly:
  - If `now` is naive (no tzinfo), treat it as UTC, then convert to America/New_York.
  - If `now` is aware, convert to America/New_York.

Implementation guidance (to reduce fragile diffs):
- Create NEW module: src/tradingbot/utils/market_hours.py
- Export it from src/tradingbot/utils/__init__.py (small edit)
- Add NEW tests file: tests/test_market_hours_guard.py
- Do NOT rewrite tests/test_smoke.py unless strictly necessary.
- Do NOT duplicate the guard inside run.py; keep it in utils.

Acceptance:
- ruff check . passes
- pytest -q passes
