# Task 047 — Verification Plugins / Validators

## Goal

Support project-specific validators beyond `ruff` and `pytest` through config/adapter-driven validator plugins.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/validator_runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `agents/run_task.py`
- `tests/test_validator_plugins.py`
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Required behavior

Support configurable validators such as:

- CLI smoke checks
- snapshot checks
- schema validators
- API contract validators
- UI screenshot/render validators

The core engine should not hardcode specific project validators.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least one non-ruff/non-pytest validator path is exercised deterministically
