# Task 141 — Orchestrator escalation artifact and supervised handoff lane

## Goal
When a task falls outside the safe autonomy lane, emit a clean escalation artifact so the orchestrator stops honestly and hands the task back in a structured way instead of failing ambiguously.

## Scope
- escalation artifact with reason, implicated files, and next supervised action
- self-hosting control-plane tasks remain escalation-first
- bounded handoff only, not broad manual patch automation

## Create or update these exact files
- `agents/run_single_task.py`
- `agents/run_task.py`
- `tests/test_single_task_runner.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/README.md`

## Required behavior
The escalation lane should produce a stable artifact describing why a task was not autonomous-safe, what files or task families triggered the escalation, and what the next supervised/manual action should be. This keeps the orchestrator useful even when it cannot safely proceed on its own.

## Acceptance
This task is complete when blocked or escalated runs emit a deterministic supervised handoff artifact, tests cover the handoff surface, and the docs describe the safe-lane boundary and escalation posture clearly.
