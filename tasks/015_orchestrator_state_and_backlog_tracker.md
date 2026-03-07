# Task 015: Orchestrator state + backlog tracker

## Goal
Build the first layer of the delivery orchestrator: a backlog/state tracker that knows what tasks exist, what state they are in, and what task should run next.

## Deliverables
- `src/builder/orchestrator/state.py`
  - dataclasses or models for:
    - task status
    - task metadata
    - orchestrator state

- `src/builder/orchestrator/backlog.py`
  - functions or classes to:
    - scan a tasks directory
    - infer task order from numeric prefixes
    - determine next pending task

- `tests/test_orchestrator_backlog.py`

## Scope
This task is about state tracking only.
Do **not** run git, PR, CI, or agent execution yet.

## Required behavior
### Task discovery
The backlog tracker must:
- scan a configured tasks directory
- detect task files with numeric prefixes such as:
  - `001_*`
  - `015_*`
- sort tasks numerically

### Task status model
Support at least these statuses:
- pending
- running
- succeeded
- failed
- merged
- blocked
- skipped

### Next-task selection
Provide a method/function that returns the next task to run.
For v1:
- select the lowest-numbered pending task

### State persistence
Use a simple file-based approach for v1:
- JSON file is acceptable

## Portability requirement
Do not hardcode TradingBot-specific task names.
The tracker should work for any repo with a numbered task directory.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- backlog ordering is deterministic
- next-task selection is deterministic
