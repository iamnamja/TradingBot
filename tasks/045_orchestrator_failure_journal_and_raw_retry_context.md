# Task 045 — Structured Failure Journal and Raw Retry Context

## Goal

Persist classified failures, repeated failure fingerprints, raw failure snippets, and chosen remediation paths to improve retries and postmortems.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Required behavior

The failure journal must record at least:

- task identifier
- failure category
- retry count
- failure fingerprint
- bounded raw failure snippet
- recommended next action
- chosen remediation path

The retry loop may use the raw snippet in the next retry context, but should keep it bounded and focused.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- repeated failure patterns are journaled and reusable
