# Task 149 — Orchestrator external safe corpus and evaluation manifest

## Goal
Define the first external-style ordinary-task evaluation corpus so the orchestrator can be measured on real one-task execution quality instead of only proof-shaped self-hosting tasks.

## Scope
- external-style safe tasks only
- no widening into arbitrary self-hosting control-plane edits
- establish corpus structure, archetype labels, and pass/fail accounting inputs

## Create or update these exact files
- `agents/lib/task_eval_corpus.py`
- `agents/run_task.py`
- `tests/test_task_eval_corpus.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_PHASE_DIRECTION.md`

## Required behavior
The repo should be able to define a small evaluation corpus of ordinary safe tasks such as focused feature work, targeted tests, constrained docs, and ordinary bug fixes. Each corpus item should carry an archetype label, allowed execution lane, and expected validation profile so later tasks can measure autonomous completion quality consistently.

## Acceptance
This task is complete when the orchestrator has a canonical external-safe evaluation manifest that future one-task autonomous runs can use as the measured proving ground for execution quality and self-heal reliability.
