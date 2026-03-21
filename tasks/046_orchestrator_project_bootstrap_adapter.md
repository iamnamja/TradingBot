# Task 046 — Project Bootstrap Adapter

## Goal

Add a bootstrap command that scaffolds a new project adapter/config/task-template set for a new repository.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/project_adapter.py`
- `src/builder/orchestrator/project_config.py`
- `agents/run_task.py`
- `tests/test_project_bootstrap_adapter.py`
- `README.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Required behavior

Bootstrap should create a minimal reusable starting point for a new client project, including:

- project config skeleton
- adapter factory skeleton
- task folder skeleton
- default validator config
- starter docs/task template references

This should reduce manual setup when using the orchestrator outside TradingBot.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a new project adapter/config scaffold can be generated deterministically
