# Task 003: Market hours guard

## Goal
Add a deterministic “market hours guard” for US equities regular trading hours (RTH) and tests.

**RTH definition (for now):**
- Monday–Friday only (no holidays yet)
- 9:30am <= time < 4:00pm in America/New_York

## Important constraints
To keep this task small and avoid churn:
- **DO NOT edit** `src/tradingbot/run.py`
- **DO NOT edit** `src/tradingbot/utils/__init__.py`
- Implement logic in a new module and add tests only.

## Scope
1) Add `src/tradingbot/utils/market_hours.py` exporting:
   - `market_hours_guard(now: datetime, calendar_source: object | None = None) -> tuple[bool, str]`

Rules:
- If `now` is timezone-aware: convert to America/New_York then evaluate.
- If `now` is naive: treat as **UTC**, then convert to America/New_York.
- Return `(True, "market open")` if within RTH.
- Otherwise return `(False, one of:)`
  - `"market closed: weekend"`
  - `"market closed: before open"`
  - `"market closed: after close"`

2) Ensure tests can import the src package:
- If `tests/conftest.py` does not exist, create it to add `<repo>/src` to `sys.path`.

3) Add tests in `tests/test_market_hours_guard.py` verifying boundary behavior:
- Mon 09:29 NY => closed before open
- Mon 09:30 NY => open
- Mon 15:59:59 NY => open
- Mon 16:00 NY => closed after close
- Sat 12:00 NY => closed weekend
- Naive UTC `2023-08-07 13:30:00` => 09:30 NY => open

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- Patch applies cleanly with `git apply -`

## Notes
- No holiday calendar yet (placeholder parameter only).
