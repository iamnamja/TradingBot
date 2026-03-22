# Task 052 — Orchestrator Second Project Portability Proof

## Goal

Prove that the orchestrator can bootstrap and reason about a second non-TradingBot project fixture without relying on TradingBot-specific assumptions.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/fixtures/sample_app/project_config.json`
- `tests/fixtures/sample_app/tasks/001_sample_task.md`
- `tests/test_second_project_portability.py`
- `README.md`

## Required behavior

1. add a minimal second project fixture that is clearly not TradingBot-specific
2. prove bootstrap/config/adapter behavior works against that fixture
3. prove validator selection and protected-file settings come from the fixture config/adapter, not TradingBot hardcoding

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- `tests/test_second_project_portability.py` proves the engine can reason about the second project fixture
- no TradingBot-specific path assumptions are required for the second project test to pass
