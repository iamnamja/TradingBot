# Task 047 — Verification Plugins / Validators

## Goal

Support project-specific validators beyond `ruff` and `pytest` through config/adapter-driven validator plugins.

Continue shrinking `agents/run_task.py` by extracting validator orchestration into `agents/lib/validator_runner.py` and preserving the shell as a thin wrapper.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/validator_runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `agents/run_task.py`
- `tests/test_validator_plugins.py`
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=run_checks
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_validator_runner_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

Do not remove or weaken the current public `run_checks()` surface.

The goal is:
- validator orchestration lives in `agents.lib.validator_runner`
- `agents.run_task.run_checks()` remains a thin compatibility wrapper

## Required behavior

Support configurable validators such as:

- CLI smoke checks
- snapshot checks
- schema validators
- API contract validators
- UI screenshot/render validators

The core engine should not hardcode specific project validators.

## Test requirements

Add deterministic tests that validate:

1. at least one non-ruff/non-pytest validator path runs through the plugin system
2. plugin selection is config/adapter-driven
3. `agents.run_task.run_checks()` delegates through `agents.lib.validator_runner`
4. current wrapper/public behavior is preserved

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least one non-ruff/non-pytest validator path is exercised deterministically
- `agents/run_task.py` is thinner after delegating validator orchestration
