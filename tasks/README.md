# Task Backlog

This folder is the execution backlog for the TradingBot build. Each task is designed to be:

- Small enough to complete in a focused PR
- Testable (unit / integration-style tests)
- CI-friendly (`ruff check .` + `pytest -q`)
- Compatible with the agent runner workflow (clear inputs/outputs + acceptance criteria)

## Repo conventions (apply to all tasks)

- Source layout: `src/tradingbot/...`
- Tests: `tests/...`
- Imports in tests:
  - Prefer normal package imports: `from tradingbot...`
  - `tests/conftest.py` already adds `<repo>/src` to `sys.path` on Windows
- Keep modules small and explicit; avoid “magic” imports and `import *`.
- Anything that talks to external services **must** be mockable and must not run in tests by default.

## Task Order (recommended)

1. 001_project_structure
2. 002_config_settings
3. 003_market_hours_guard ✅ (done)
4. 004_data_layer
5. 005_indicators
6. 006_strategy_v1
7. 007_llm_advisor
8. 008_risk_gate
9. 009_execution_engine
10. 010_e2e_cycle_logging

## How to run checks locally

```powershell
py -m pip install -r requirements.txt
ruff check .
pytest -q
```
