# Task 029: Orchestrator approval checkpoint flow

## Goal
Formalize how the orchestrator stops for human approval when policy or repair logic says approval is required.

## Deliverables
- new file:
  - `src/builder/orchestrator/approval.py`
- updates to:
  - `src/builder/orchestrator/runner.py`
  - `src/builder/orchestrator/audit.py` (only if minimally needed)
- `tests/test_orchestrator_approval_flow.py`

## Existing repo dependencies (NOT deliverables)
Reuse:
- `policy.py`
- `repair.py`
- `runner.py`
- `audit.py`

Do not replace those modules wholesale.

## Required behavior

### Approval checkpoint concept
When the workflow reaches a state that requires human approval, the orchestrator must:
- stop the automated task flow
- record a structured approval checkpoint
- return a deterministic result indicating approval is required

### Required checkpoint fields
A checkpoint should contain deterministic fields such as:
- `task_name`
- `reason`
- `source`
- `requested_action`
- `status`

### Source values
The approval request should identify what triggered it, for example:
- policy
- repair
- merge_gate

### Workflow integration
This is the most important rule in the task.

The orchestrator must not continue automatically past an approval-required outcome.
It must stop cleanly and return control.

### Audit integration
The approval checkpoint should be auditable.
If audit logging is used, tests must use temp paths and not dirty the repo.

### Test guidance
Tests must cover at least:
- approval required from policy
- approval required from repair decision
- no approval needed path
- deterministic checkpoint content

Do not require live git/GitHub access.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- orchestrator stops cleanly when approval is required
- approval checkpoint output is deterministic and structured
