# Task 003 — Market Hours Guard (Safe Patch)

## Goal
Add a simple "market hours guard" function that determines whether US equities markets are open, and integrate it into the main run flow so the bot exits early if markets are closed.

## Constraints (VERY IMPORTANT)
- **DO NOT** edit `tests/test_smoke.py` (leave it exactly as-is).
- Prefer **new files** over large edits.
- Keep changes minimal and targeted.
- All code must pass:
  - `ruff check .`
  - `pytest -q`

## Required Implementation

### 1) Create market hours guard utility
Create a new module:

- `src/tradingbot/utils/market_hours.py`

It must expose:

```python
def market_hours_guard(now: datetime, calendar_source=None) -> tuple[bool, str]:
    ...
```

Behavior:
- Convert `now` to **America/New_York**
- **Open** if:
  - Weekday is Mon–Fri
  - Time is **>= 09:30** and **< 16:00** NY local time
- Otherwise **closed**
- Return `(True, "market open")` if open
- Return `(False, "...")` if closed with one of these exact reasons:
  - `"market closed: weekend"`
  - `"market closed: before open"`
  - `"market closed: after close"`

If `now` is naive, treat it as **UTC** (set tzinfo=UTC) before converting to NY.

### 2) Re-export from utils package
Update `src/tradingbot/utils/__init__.py` to export:

```python
from .market_hours import market_hours_guard
```

(Keep file minimal; do not add unrelated code.)

### 3) Integrate into run.py (minimal edit)
Update `src/tradingbot/run.py` to:
- import `market_hours_guard`
- compute `now = datetime.now(tz=ZoneInfo("UTC"))`
- call guard before placing orders
- if closed, print `Market closed: <reason>` and exit with status 0

Keep the rest of `run.py` behavior unchanged.

### 4) Add dedicated tests (new file)
Create a new test file:

- `tests/test_market_hours_guard.py`

Must include tests for:
- Monday 09:29 NY => closed: before open
- Monday 09:30 NY => open
- Monday 15:59 NY => open
- Monday 16:00 NY => closed: after close
- Saturday noon NY => closed: weekend
- Naive datetime 13:30 UTC => open (because 13:30 UTC == 09:30 NY during EDT)

## Output
Return a valid unified git patch as a single ` ```diff ` fenced block plus `COMMIT:` line, per `agents/prompts/system.md`.
