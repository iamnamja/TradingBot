# Task 105 — Orchestrator targeted repair planner and minimal-patch selection

## Why this task exists

Recent recoveries succeeded by applying small targeted fixes rather than rerunning broad rewrites.

The orchestrator should learn that discipline.

## Outcome

Add a targeted repair planner that prefers the smallest compatible patch surface for bounded failures.

## Create or update these exact files

- `agents/lib/controller_repair.py`
- `agents/lib/agent_router.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

- recognize when a failure likely needs only an alias, import correction, shape adapter, or docs sync
- prefer the smallest plausible repair surface
- preserve explicit route rationale for why a minimal patch was selected
- keep conservative stop behavior when the failure is not safely narrow

## Acceptance

This task is complete when the orchestrator can prefer narrow targeted compatibility fixes over broad rewrites for bounded repair scenarios.
