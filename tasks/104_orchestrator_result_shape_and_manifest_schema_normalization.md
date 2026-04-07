# Task 104 — Orchestrator result-shape and manifest-schema normalization

## Why this task exists

Recent failures showed brittle drift around result fields and manifest entry keys such as `path` vs `task_path`.

## Outcome

Normalize proof-facing result shapes and manifest schema through canonical adapters and compatibility surfaces.

## Create or update these exact files

- `agents/lib/manifest_planner.py`
- `agents/lib/task_queue.py`
- `agents/lib/multi_agent_loop.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_multi_project_adapters.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Required behavior

- normalize manifest entry schema in one canonical place
- normalize proof-facing loop result fields in one canonical place
- keep compatibility adapters explicit and narrow
- prefer one canonical output shape plus deliberate aliases rather than scattered ad hoc branching

## Acceptance

This task is complete when result-shape and manifest-schema drift stop causing avoidable proof-task failures.
