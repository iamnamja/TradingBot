# Task 044a — Spec Mode Capture

## Goal

Add a spec-generation mode that captures clarifications, forbidden patterns, acceptance criteria, verification commands, and expected outputs into a frozen task artifact.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/spec_mode.py`
- `agents/run_task.py`
- `tests/test_spec_mode_capture.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Required behavior

Spec mode should:

- identify when the task is underspecified
- produce a structured frozen spec artifact
- capture:
  - scope
  - edge cases
  - forbidden patterns
  - acceptance criteria
  - verification commands
  - expected outputs when available

This mode should not perform implementation work.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- a frozen spec artifact can be generated deterministically
