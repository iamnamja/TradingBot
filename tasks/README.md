# Task Backlog

This folder is the execution backlog for the TradingBot build. Each task is designed to be:
- Small enough to complete in a focused PR
- Testable (unit/integration-style tests)
- CI-friendly (ruff + pytest)
- Compatible with AI agent workflows (clear inputs/outputs and acceptance criteria)

## Task Order (recommended)
1. 001_project_structure
2. 002_config_settings
3. 003_market_hours_guard
4. 004_data_layer
5. 005_indicators
6. 006_strategy_v1
7. 007_llm_advisor
8. 008_risk_gate
9. 009_execution_engine
10. 010_e2e_cycle_logging

## Conventions
- Put implementation under `src/tradingbot/...`
- Keep a thin wrapper at repo root `bot.py` for local running convenience
- Tests under `tests/`
- No secrets in git. Use `.env` locally and GitHub Actions Secrets in CI/CD.