# Task 054 — Orchestrator Task / Seam Preflight Linter

## Goal

Add a lightweight preflight that catches common task-generation mistakes before a full iteration runs, especially around nonexistent seam names, forbidden nested validators, and canonical docs path drift.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_orchestrator_public_surface.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

Add a preflight that can flag or fail fast on at least these classes of issues in generated test/code bundles:

1. monkeypatch targets or seam names that do not exist in the live repo
2. integrated tests that would recursively invoke real repo-wide `pytest -q` or `ruff check .`
3. canonical docs path drift:
   - `README.md` at repo root
   - orchestrator/tradingbot narrative docs under `docs/`
4. obvious task/deliverable mismatch where generated files fall outside the task’s listed scope

## Compatibility constraints

- this task must be additive and safe
- it must not turn the harness into a full static analyzer
- false positives should be minimized
- if a preflight is advisory rather than blocking, that behavior should be explicit and documented

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the harness can catch at least the listed mistake classes before consuming a full iteration
- controls/policies docs explain what the preflight checks and how it reports issues
