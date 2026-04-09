# Task 146 — Orchestrator safe-lane stop, requeue, and supervised mix policy

## Goal
Teach the scheduler how to behave conservatively when a queue mixes autonomous-safe work with supervised-only or escalation-required work.

## Scope
- conservative one-task-at-a-time queue handling only
- explicit stop/requeue semantics
- no broad batch autonomy claim

## Create or update these exact files
- `agents/lib/batch_executor.py`
- `agents/lib/task_queue.py`
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_task_queue.py`
- `tests/test_single_task_runner.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior
If one safe task is ready while other tasks are supervised-only or escalation-required, the system should run at most the single safe task, emit explicit handoff for blocked work, requeue what remains appropriately, and stop without inventing broader autonomy.

## Acceptance
This task is complete when mixed queues produce deterministic conservative behavior: at most one safe run, explicit supervised handoff for unsafe work, and no ambiguity about stop versus requeue posture.
