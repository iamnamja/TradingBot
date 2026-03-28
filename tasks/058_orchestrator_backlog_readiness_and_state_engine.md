# Task 058 — Orchestrator Backlog Readiness and State Engine

## Goal

Promote backlog readiness, blockers, and next-task selection into first-class orchestrator behavior.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/backlog_state.py`
- `src/builder/orchestrator/orchestrator_runtime.py`
- `tests/test_orchestrator_resume_after_approval.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_resume_after_approval.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

The orchestrator should be able to represent at least:

- ready
- blocked
- waiting for approval
- manual-patch lane
- completed
- deferred

And should be able to determine the next ready task without rescanning the world in ad hoc ways.

The state engine should retain enough context for the remediation planner and autonomy loop to resume after interruption.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- backlog state/readiness concepts are represented explicitly in orchestrator runtime/state code and docs
