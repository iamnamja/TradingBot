# Task 048 — Safe Parallelism

## Goal

Allow limited parallel execution only for task classes explicitly marked independent and safe.

This work should live in the reusable orchestrator engine layer, not in `agents/run_task.py`, unless a later follow-up explicitly introduces additive shell routing.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/project_config.py`
- `src/builder/orchestrator/project_adapter.py`
- `tests/test_safe_parallelism.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

Parallel execution must default to off.

It is allowed only when the task class is explicitly marked parallel-safe and the tasks do not overlap on protected files or shared mutable state.

## Required behavior

Safe parallelism must include:

- explicit opt-in
- deterministic grouping of independent tasks
- prohibition on overlapping protected files
- prohibition on bypassing approval policy
- deterministic fan-in / reporting order

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- parallel mode remains off by default
- independent-task parallel execution is validated without weakening policy
