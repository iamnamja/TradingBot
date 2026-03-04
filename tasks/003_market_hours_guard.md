# Task 003 — Market Hours Guard (hardened)

Goal: add a reusable `market_hours_guard()` helper and tests **without breaking CI**.

## IMPORTANT FORMAT
You MUST output a file bundle with these exact markers, and NOTHING else:
- BEGIN_FILE_BUNDLE
- FILE: <path>
- <content>
- END_FILE
- END_FILE_BUNDLE

If there are no changes needed, output an EMPTY bundle:
BEGIN_FILE_BUNDLE
END_FILE_BUNDLE

## Repo context assumptions (src layout)
- Python package lives under `src/`
- Imports should use `tradingbot...` (NOT `src.tradingbot...`)
- Tests must be able to import from `src/` (there is already `tests/conftest.py` adding `<repo>/src` to `sys.path`; if missing, add it).

## Implementation rules (CI / ruff friendly)
- Do NOT add unused imports.
- If you edit `src/tradingbot/utils/__init__.py` and you re-export `market_hours_guard`, you MUST also set:
  - `__all__ = ["market_hours_guard"]`
  - and/or use `# noqa: F401` to avoid ruff F401.
- Do NOT import `pytest` unless you actually use it.

## Required end-state
1) `src/tradingbot/utils/market_hours.py` exists and defines:

`market_hours_guard(now: datetime, calendar_source=None) -> tuple[bool, str]`

Behavior:
- Convert `now` to America/New_York
- If `now` is naive: treat it as UTC first, then convert to NY
- Weekend (Sat/Sun) => `(False, "market closed: weekend")`
- Before 09:30 NY => `(False, "market closed: before open")`
- At/after 16:00 NY => `(False, "market closed: after close")`
- Otherwise => `(True, "market open")`

2) Tests:
- Add `tests/test_market_hours_guard.py` with simple `assert` tests (no pytest import needed).
- Cover before open, at open, just before close, at close, weekend, naive UTC conversion.

3) Integration:
- If `tradingbot.run` currently has an inline `market_hours_guard`, remove it and import from `tradingbot.utils.market_hours`.
- If there is no inline guard, do not change run.py.

## What to change (minimal)
- Prefer: only create missing files and minimal imports.
- If all required files already exist and CI is green, output EMPTY bundle.
