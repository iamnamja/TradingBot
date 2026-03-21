# Task 044b — Frozen Execution Mode

## Goal

Run the normal task execution workflow against a frozen spec artifact instead of an ambiguous raw task when spec mode has already been used.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_execution_mode_frozen_task.py`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Required behavior

Execution mode should:

- accept a frozen spec artifact as the canonical task input
- preserve current execution behavior once the task is frozen
- keep the distinction between planning/spec work and implementation work visible in logs/audit

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- execution can proceed deterministically from a frozen spec artifact
