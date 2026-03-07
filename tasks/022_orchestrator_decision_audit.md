# Task 022: Orchestrator decision audit and journal

## Goal
Add an audit/journal layer so every important orchestrator decision is recorded in a structured, inspectable way.

## Deliverables
- `src/builder/orchestrator/audit.py`
  - functions/classes to write orchestrator decision events

- `tests/test_orchestrator_audit.py`

## Required behavior
### Audit events
Record events for at least:
- selected task
- classification result
- review verdict
- PR action
- merge decision
- repair decision
- stop/escalation decision

### Storage
For v1, use a simple local file-based format:
- JSON or JSONL is acceptable

### Determinism
Audit output should be structured and deterministic enough for tests.

### Safety
Tests must not dirty the repo with runtime artifacts.
Use temp directories in tests.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- audit events are written and readable
- tests use temp paths rather than repo-root artifact directories
