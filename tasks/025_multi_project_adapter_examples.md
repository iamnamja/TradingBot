# Task 025: Multi-project adapter examples

## Goal
Prove that the orchestrator is reusable by adding at least one additional project adapter example besides TradingBot.

## Deliverables
- updates to:
  - `src/builder/orchestrator/project_config.py`
  - `src/builder/orchestrator/project_adapter.py`
- `tests/test_multi_project_adapters.py`

## Required behavior
### Adapters
Provide:
- TradingBot adapter
- one additional generic example adapter

The second adapter can be simple, but it must demonstrate:
- different tasks directory
- different lint/test commands or patterns
- different protected/artifact rules

### Goal
This task is about proving portability, not integrating a real second repo.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- project-specific behavior is adapter-driven, not engine-hardcoded
