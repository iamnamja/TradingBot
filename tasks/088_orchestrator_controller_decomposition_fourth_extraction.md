# Task 088 — Orchestrator controller decomposition fourth extraction

## Why this task exists

`agents/run_task.py` is thinner than before, but it still owns too much controller glue around strict mode, repair digests, and controller-task orchestration.

## Outcome

Perform another deliberate extraction pass so more controller families move out of `agents/run_task.py` without breaking compatibility.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/controller_contract.py`
- `agents/lib/controller_repair.py`
- `agents/lib/controller_strict_mode.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/task_contracts.py`
- `docs/orchestrator_extraction_plan.md`
- `tests/test_run_task_runtime_foundations.py`

## Required behavior

### 1) Extract more controller families

Move additional controller-family helpers out of `agents/run_task.py`, especially around:

- controller strict-mode decisions
- semantic failure digest wiring
- controller repair-context construction
- post-acceptance feedback/report surfaces

### 2) Keep compatibility wrappers

`agents/run_task.py` may keep small compatibility wrappers, but the real behavior should live in extracted helper modules.

### 3) Honest extraction plan update

Update the extraction plan to reflect what is now extracted and what still remains inline after this pass.

## Tests

Add or adjust tests that prove the `run_task.py` shell wrappers delegate to extracted helpers for the newly moved controller families.

## Guardrails

- Do not perform a risky all-at-once split
- Keep module boundaries explicit and reviewable
- Preserve public surface compatibility unless a task explicitly changes it

## Acceptance

This task is complete when `agents/run_task.py` is materially thinner again and the extraction plan is updated honestly.
