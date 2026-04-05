# Task 093 — Orchestrator repair strategy router and failure-lane selection

## Why this task exists

Task 086 added a semantic controller failure digest, but the orchestrator still needs a stronger remediation planner that can choose the right repair lane instead of treating every failure as the same kind of coding problem.

For a builder/verifier/controller architecture, repair strategy selection must become more explicit.

## Outcome

Add a repair-strategy router that chooses the right remediation lane based on semantic failure type.

## Create or update these exact files

- `agents/lib/controller_repair.py`
- `agents/lib/failure_journal.py`
- `agents/lib/multi_agent_loop.py`
- `agents/lib/final_acceptance.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical repair lanes

At minimum support explicit strategy selection for:

- syntax / import / lint failures
- failing test / behavioral regression failures
- controller contract drift failures
- environment / setup / bootstrap failures
- CI-only or merge-posture failures
- docs / proof-claim drift failures

### 2) Role-aware repair routing

The controller should be able to decide whether the next action belongs to:

- builder role
- verifier role
- operator/manual lane

### 3) Failure-journal alignment

Failure journaling and remediation planning must use the same strategy vocabulary.

### 4) Conservative stop posture

Failures that are not safely repairable should remain truthful stop signals.

## Tests

Add or adjust deterministic tests that prove:

1. semantic failure categories map to explicit repair strategies
2. controller chooses the correct role/lane for the next remediation step
3. non-repairable failures still stop honestly
4. failure journal entries and repair-router decisions do not drift

## Guardrails

- Do not turn every failure into a blind builder retry
- Keep repair strategies explicit and inspectable
- Preserve non-reexecuting self-heal truth from 084
- Prefer a small number of strong canonical lanes over many ad hoc categories

## Acceptance

This task is complete when failure handling is routed through explicit repair strategies and role-aware remediation lanes rather than one generic retry surface.
