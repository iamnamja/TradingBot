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

### Writer/path contract
This is the most important rule in this task.

The audit layer must be testable with temp paths.
Do **not** hardwire repo-root paths inside the event-writing functions.

Acceptable patterns:
- pass `audit_path` explicitly to write functions
- pass an audit writer object
- provide a configurable default that tests can override deterministically

Tests must be able to direct all writes into a temp file or temp directory.

### Append + flush semantics
Each event write must:
- append to the target sink/file
- make the written event visible to the immediately following read in tests

### Event shape
Every event should include at least:
- `event`
- `timestamp`
- event-specific payload fields

### Time handling
Use timezone-aware UTC timestamps rather than deprecated naive `utcnow()` behavior.

### Determinism
Audit output should be structured and deterministic enough for tests.
Event names must match the expected strings exactly.

### Safety
Tests must not dirty the repo with runtime artifacts.
Use temp directories/files in tests.

## Normative examples
Example 1:
- `log_selected_task("test_task", audit_path=tmp_file)` writes an event whose `event` is `selected_task`

Example 2:
- `log_merge_decision("merge", audit_path=tmp_file)` appends a readable event to the same file

Example 3:
- immediately opening the temp file after the write shows the event content

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- audit events are written and readable
- tests use temp paths rather than repo-root artifact directories
- implementation follows the writer/path contract above
