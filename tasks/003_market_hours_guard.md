# Task 003: Market hours guard (US equities RTH)

Goal: add a reusable helper `market_hours_guard` and tests.

Constraints:
- Do not edit `src/tradingbot/run.py` unless it already has inline market hours logic that should be moved.
- Place the guard in: `src/tradingbot/utils/market_hours.py`
- Export it from: `src/tradingbot/utils/__init__.py` (safe, minimal change)
- Add unit tests in: `tests/test_market_hours_guard.py`
- Do NOT add `tests/conftest.py` for sys.path hacks. The project should already be importable in CI.
  - Import the module as `from tradingbot.utils.market_hours import market_hours_guard`.
  - If imports fail, fix packaging the correct way (but keep changes minimal).

Behavior:
- Input: `now: datetime`
- If `now` is naive: assume UTC, convert to America/New_York.
- If aware: convert to America/New_York.
- Weekend (Sat/Sun): closed -> ("market closed: weekend")
- Weekday:
  - before 09:30:00 NY time -> ("market closed: before open")
  - at/after 16:00:00 NY time -> ("market closed: after close")
  - otherwise -> ("market open")

Return: tuple[bool, str] where bool is open/closed and str is exact reason above.

Tests:
- at least these cases:
  - Monday 09:29 NY -> closed before open
  - Monday 09:30 NY -> open
  - Monday 15:59:59 NY -> open
  - Monday 16:00 NY -> closed after close
  - Saturday noon NY -> closed weekend
  - naive UTC datetime 13:30 UTC on Monday (== 09:30 NY during EDT) -> open

Also:
- Make sure ruff passes (no unused imports).
- Do not change unrelated tests.

Deliverables:
- Implement `src/tradingbot/utils/market_hours.py`
- Update `src/tradingbot/utils/__init__.py` to export the function
- Add `tests/test_market_hours_guard.py`

Remember: output as FILE BUNDLE ONLY (see system prompt).
