# Task 024: Orchestrator policy engine

## Goal
Formalize approval gates and automation boundaries into a policy engine rather than scattering the rules across the orchestrator.

## Deliverables
- `src/builder/orchestrator/policy.py`
  - policy evaluation logic

- `tests/test_orchestrator_policy.py`

## Required behavior

### Policy inputs
Support evaluation against:
- changed files
- failure category
- requested repair action
- project config / protected-file patterns

### Required outputs
Return structured policy decisions such as:
- allowed
- blocked
- requires_approval

### Policy precedence
This is the most important rule in this task.

If multiple rules apply, precedence should be:
1. blocked
2. requires_approval
3. allowed

For example:
- a protected-file violation should block even if another rule would otherwise allow
- an approval-required case should not be downgraded to allowed

### Required cases
The engine must handle:
- protected file modifications
- workflow/CI changes
- dependency changes
- live-trading related changes
- ordinary safe task outputs

### Determinism
Policy decisions must be deterministic and based on explicit inputs only.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- policy decisions are deterministic
- approval-required cases are clearly identified
- precedence follows the rule above
