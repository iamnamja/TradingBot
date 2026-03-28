# Task 056 — Orchestrator Failure Classifier and Remediation Planner

## Goal

Turn failed runs into structured remediation decisions instead of sending every failure back through the same retry loop.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=main TARGET_ANCHOR=def main(
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

Introduce structured failure classes such as:

- syntax-only failure
- file-local semantic failure
- task-shape mismatch
- seam-contract mismatch
- harness/meta regression
- CI-only failure
- manual-lane escalation

Map these classes to remediation plans such as retry, local repair, task patch, runner patch, split recommendation, stop, or manual patch lane.

Include confidence-gated autonomy decisions so the orchestrator knows when to continue alone and when to escalate.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py` passes
- the orchestrator can distinguish at least three failure classes and choose different remediation plans
