# Task 150 — Orchestrator one-task multi-agent dev / test / repair loop

## Goal
Make the bounded one-task lane behave like a real multi-agent execution loop by separating developer, tester, repair, and controller responsibilities inside one safe autonomous task run.

## Scope
- one task at a time only
- no broad multi-task scheduler expansion
- preserve explicit supervision for self-hosting control-plane work

## Create or update these exact files
- `agents/lib/controller.py`
- `agents/lib/verifier.py`
- `agents/lib/repair_loop.py`
- `agents/run_single_task.py`
- `tests/test_single_task_runner.py`
- `tests/test_repair_workflow.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_RELIABILITY_AND_AUTONOMY_REVIEW.md`

## Required behavior
A bounded one-task run should clearly separate: generation, focused validation, full validation, failure critique, targeted repair attempt selection, and controller decision. The run record should make it clear which role produced which decision and which evidence triggered a retry or escalation.

## Acceptance
This task is complete when one-task autonomous execution is no longer just a shell around patch generation, but a bounded multi-agent loop with explicit dev/test/repair/controller stages and deterministic role-specific artifacts.
