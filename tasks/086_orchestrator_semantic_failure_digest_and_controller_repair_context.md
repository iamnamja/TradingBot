# Task 086 — Orchestrator semantic failure digest and controller repair context

## Why this task exists

Controller-core tasks still fail because the repair loop gets raw failing output but not a strong semantic summary of what actually drifted.

The orchestrator needs a structured failure digest that is rich enough to guide repairs across multiple controller modules.

## Outcome

Create a semantic failure digest module for controller-task failures and use it to generate focused controller repair context.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/controller_repair.py`
- `agents/lib/failure_journal.py`
- `agents/lib/final_acceptance.py`
- `agents/run_task.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Structured failure digest

For controller-task failures, the orchestrator should be able to summarize at least:

- failing test names
- actual vs expected decision strings
- missing or extra persisted truth fields
- missing public wrapper/helper exports
- merge-posture mismatch
- policy/controller taxonomy mismatch
- exact controller-family files touched

### 2) Controller repair context

The repair loop should be able to turn the semantic failure digest into a focused repair prompt/context instead of handing the model only raw failing output.

### 3) Reuse of digest

The digest should be reusable by:

- final acceptance/self-heal feedback
- controller strict mode
- failure journaling/history

## Tests

Add or adjust tests that prove:

1. controller-task failures can be normalized into a semantic digest
2. repair context names the key drift surfaces rather than only raw stack traces
3. controller-focused failure digest remains machine-readable and stable

## Guardrails

- Do not remove raw failing output; add semantic digest on top of it
- Keep digest deterministic and compact
- Keep the real logic in a helper module rather than expanding `agents/run_task.py`

## Acceptance

This task is complete when controller-task repair can consume a semantic failure digest instead of relying only on raw failing logs.
