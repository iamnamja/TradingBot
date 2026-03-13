# Task 033 — Real Review and Compliance Gate

## Goal

Evaluate actual execution results and changed files through a policy engine before allowing merge readiness.

## Why

Once execution is real, review must use real execution outputs — not just the presence of changed files. A policy engine determines whether changed files require approval before merging.

## Critical compatibility requirement

All existing public APIs must remain backward compatible. Do not change:
- `OrchestratorRunner.__init__` signature
- `run_next_task(dry_run=False)` signature
- `process_execution_result(execution_result, task)` signature
- `simulate_backlog()` signature or return contract

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/review.py`
- `src/builder/orchestrator/policy.py`
- `tests/test_orchestrator_real_review_gate.py`

All four files must be materially updated in the same bundle.

## Bundle completeness requirement

The bundle is incomplete unless all four deliverables are present.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
`processed_tasks`, `stopped_reason`, `final_status`, `approval_required`, `planned_actions`

## Required behavior

### policy.py

Must define a `PolicyEngine` class with:

```python
class PolicyEngine:
    def __init__(self, approval_required_patterns: list[str]) -> None: ...
    def requires_approval(self, changed_files: list[str]) -> bool: ...
```

`requires_approval` returns `True` if any changed file matches any approval-required pattern.

### review.py updates

`ReviewChecker` must use `PolicyEngine` to determine if approval is required based on changed files.

`ReviewChecker.evaluate()` must return a dict with at least:
```python
{
    "mergeable": bool,
    "approval_required": bool,
    "reason": str,
}
```

### runner.py integration

`run_review` must pass changed files through `PolicyEngine` in addition to existing review logic.

Review outcome must be one of:
- `mergeable` — execution succeeded, review passed, policy allows merge
- `review_blocked` — review did not pass
- `approval_required` — policy requires human approval

## Exact legacy contract that must not be changed

When a pending task exists on the legacy/mock success path:
- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`
- `requires_approval == False`

When review is blocked:
- `status == "running"`
- `message == "Task is now running."`
- `requires_approval == True`
- `outcome == "review_blocked"`

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`
- `next_action == "require_human_review"`

## CRITICAL — simulate_backlog must be implemented exactly

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    result = self.process_execution_result(execution_result, next_task)

    if result["status"] == "failed":
        stopped_reason = execution_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

`requires_approval` must be derived from `run_review` result, not from empty `changed_files`.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- `if not effective_changed: return {"mergeable": False}` in `run_review`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- unused local variables that ruff will flag
- `@dataclass(frozen=True)` on any config class

## Acceptance criteria

Tests in `tests/test_orchestrator_real_review_gate.py` must cover:

- mergeable success path
- missing deliverables triggering review block
- approval-required file changes
- no changed files edge case (must still be mergeable on mock path)

`ruff check .` must pass. `pytest -q` must be fully green.
