# Task 020: Generic project adapter layer

## Goal
Make the orchestrator reusable for future software projects by separating generic engine behavior from project-specific configuration.

## Deliverables
- `src/builder/orchestrator/project_config.py`
  - project config schema/model

- `src/builder/orchestrator/project_adapter.py`
  - adapter layer for project-specific behavior

- `tests/test_project_adapter.py`

## Required behavior
### Project config
Support configuration of:
- tasks directory
- lint command
- test command
- branch naming pattern
- protected file patterns
- artifact path patterns
- approval-required file patterns

### Project adapter
Provide methods that translate project config into orchestrator behavior.

### TradingBot adapter
Include a TradingBot-compatible example/default configuration.

## Portability requirement
The orchestrator engine should not need TradingBot-specific hardcoding once this adapter is in place.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- project adapter works for TradingBot defaults
- design is generic enough for future repos
