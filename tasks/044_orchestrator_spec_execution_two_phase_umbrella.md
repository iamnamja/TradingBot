# Task 044 — Spec / Execution Two-Phase Workflow (Umbrella)

## Status

Do NOT run this umbrella task directly with the agent.

## Goal

Separate ambiguous-task clarification from implementation while continuing to shrink `agents/run_task.py` into a thin shell over extracted helper modules.

## Run order

1. `tasks/044a_orchestrator_spec_mode_capture.md`
2. `tasks/044b_orchestrator_execution_mode_frozen_task.md`

## Why

Recent tasks repeatedly showed that many retries were caused by baseline-guessing and task ambiguity rather than raw coding failure.

This tranche formalizes:
- **Spec mode** — clarify and freeze the task
- **Execution mode** — implement only the frozen task

Both tasks should prefer:
- reusable helper modules under `agents/lib/`
- additive/narrow shell changes in `agents/run_task.py`
- no broad CLI rewrite
