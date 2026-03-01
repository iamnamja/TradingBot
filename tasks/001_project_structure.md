# Task 001: Project structure + entrypoints

## Goal
Move the project into a clean Python package structure so the bot is runnable as:
- `py bot.py` (wrapper entrypoint)
- `py -m tradingbot.run` (package entrypoint)

## Scope
- Create package layout under `src/tradingbot/`
- Keep `bot.py` at repo root as a thin wrapper that calls `tradingbot.run:main`
- Ensure imports are package-safe and do not rely on cwd quirks
- Keep current Alpaca smoke behavior working (account fetch + example order)

## Proposed Structure
src/
  tradingbot/
    __init__.py
    run.py                 # main entrypoint
    config/
      __init__.py
    brokers/
      __init__.py
    runtime/
      __init__.py
    utils/
      __init__.py
bot.py                     # wrapper calls tradingbot.run.main()
tests/
  test_smoke.py

## Acceptance Criteria
- `py -m tradingbot.run` starts without errors (with `.env` present)
- `py bot.py` also works (same behavior)
- `ruff check .` passes
- `pytest -q` passes
- CI runs on PR and main

## Tests
- Update `tests/test_smoke.py` if needed to import from package (`tradingbot...`)
- Add a lightweight test that `tradingbot.run` exposes `main()` and can be imported
  (avoid live network calls in CI by guarding with env flags / mocking)

## Notes for Agents
- Keep network calls out of tests by default
- Use dependency injection or a `DRY_RUN`/`LIVE_API_CALLS=false` guard for CI