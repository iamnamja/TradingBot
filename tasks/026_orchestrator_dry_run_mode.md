# Task 026: Orchestrator dry-run mode

## Goal
Add a dry-run / simulation mode so the orchestrator can show what it would do without mutating repo or PR state.

## Deliverables
- updates to orchestrator runner/CLI as needed
- `tests/test_orchestrator_dry_run.py`

## Required behavior

### Dry-run mode
The orchestrator should:
- load config and state
- select the next task
- evaluate what actions would be taken
- print or return a structured plan
- avoid mutating git branches, PRs, or remote state

### Mutation boundary
This is the most important rule in this task.

In dry-run mode, the orchestrator must not call mutation methods such as:
- create branch
- push branch
- create PR
- merge PR
- write remote state

Tests should verify these mutation methods are not called.

### Audit
Dry-run decisions should still be auditable through the decision journal.

### Safety
Dry-run mode must not create remote branches, PRs, or merges.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- dry-run mode does not mutate external state
- dry-run output clearly communicates the intended actions
- tests verify the mutation boundary above
