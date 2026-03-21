# Task 043 — Runtime Artifact Quarantine

## Goal

Automatically quarantine known safe runtime artifacts before final commit/merge while preserving warnings and audit visibility.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/artifact_quarantine.py`
- `agents/run_task.py`
- `tests/test_runtime_artifact_quarantine.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

All listed files must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical behavior

Known safe artifacts should be auto-unstaged and deleted before final commit/merge when recoverable, while still being surfaced in warnings/audit output.

Examples of known safe artifacts include:

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

Unknown artifacts must still fail or block as policy requires.

## Test requirements

Add deterministic tests for:

1. safe known artifact auto-quarantine
2. warning/audit visibility preserved after quarantine
3. unknown artifact still blocks appropriately
4. quarantined artifacts do not silently disappear from decision output

## Exact forbidden patterns

- silently ignoring unknown artifacts
- weakening merge policy
- touching orchestrator engine files under `src/builder/orchestrator/`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- known safe artifacts no longer require manual cleanup before PR
- warnings/audit behavior remains intact
