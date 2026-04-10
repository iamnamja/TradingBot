# Task 154 — Orchestrator two-task readiness gate and phase transition

## Goal
Decide whether the orchestrator has earned the right to start bounded two-task or short-chain trials, based on measured one-task external-safe performance rather than optimism.

## Scope
- phase gate only
- no immediate broad multi-task rollout
- keep self-hosting control-plane autonomy out of scope

## Create or update these exact files
- `agents/lib/task_queue.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PHASE_DIRECTION.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/NEW_CHAT_HANDOFF_PROMPT.md`

## Required behavior
The repo should define explicit entry criteria for the next phase, such as minimum one-task pass rate, acceptable escalation rate, acceptable authority-block rate, and confidence that the multi-agent repair loop is no longer the dominant source of manual patching.

## Acceptance
This task is complete when the project has a documented go / no-go gate for bounded two-task autonomy, grounded in measured one-task external-safe results rather than in untested ambition.
