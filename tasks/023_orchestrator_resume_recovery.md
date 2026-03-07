# Task 023: Orchestrator resume and recovery

## Goal
Enable the orchestrator to recover safely after interruption and continue from persisted state.

## Deliverables
- `src/builder/orchestrator/recovery.py`
  - recovery logic and helpers

- `tests/test_orchestrator_recovery.py`

## Required behavior

### Recovery scenarios
Support at least:
- previously running task found in state
- partially written state file
- stale branch or stale in-progress marker
- already-merged task state

### Required outcome
The recovery logic should decide whether to:
- resume
- reset task to pending
- mark blocked
- require human review

### Deterministic recovery contract
The recovery layer should be a pure decision layer for v1.
Do not perform live git/GitHub side effects in these unit tests.

Inputs should be explicit structured values such as:
- current state
- parse/read error flags
- branch presence flags
- merge status flags

Outputs should be deterministic structured decisions.

### Safety
Do not assume interrupted work is safe to continue blindly.
Prefer deterministic recovery decisions.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- recovery decisions are deterministic for provided scenarios
- tests do not require live git/GitHub access
