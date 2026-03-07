# Task 019: Repair workflow for task specs / runner

## Goal
Build the workflow logic that handles repair cases when the orchestrator determines that a failure is caused by task ambiguity, runner weakness, CI issues, or repo hygiene problems.

## Deliverables
- `src/builder/orchestrator/repair.py`
  - repair decision logic
  - approval gating logic

- `tests/test_repair_workflow.py`

## Required behavior
### Inputs
Use:
- failure classification
- changed-file patterns
- configurable approval-required file patterns

### Required actions
Support:
- patch_task
- patch_runner
- patch_ci
- clean_repo
- require_human_review

### Approval gates
Human approval must be required for:
- task runner changes
- workflow/CI changes
- dependency management changes
- secrets/auth changes
- live-trading related safety changes

### Output
Return structured repair decisions with:
- action
- requires_approval
- reason

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- repair workflow enforces approval requirements deterministically
