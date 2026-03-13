# Task 034 — Branch and Worktree Guardrails

## Goal

Prevent orchestrator real execution in unsafe git states. Simulation mode must bypass all guardrails.

## Why

Real execution should never run on `main`, with a dirty worktree, or on a branch that doesn't match the expected task branch pattern. These guardrails prevent accidental commits to protected branches.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- Simulation mode must bypass all guardrails — existing simulation tests must not be broken

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/git_guardrails.py`
- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_git_guardrails.py`

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

### git_guardrails.py

Must define a `GitGuardrails` class:

```python
class GitGuardrails:
    def __init__(self, branch_naming_pattern: str) -> None: ...
    def check(self) -> tuple[bool, str]:
        """Returns (safe: bool, reason: str)"""
```

`check()` must fail (return `False`) when:
- current branch is `main`
- worktree has uncommitted changes (`git status --porcelain` is non-empty)
- current branch name does not match `branch_naming_pattern`

`check()` must pass (return `True`) when:
- on a valid non-main branch matching the pattern
- worktree is clean

### runner.py integration

`run_next_task()` must call `GitGuardrails.check()` before executing a task.

If the check fails, `run_next_task()` must return:
```python
{
    "task_name": "none",
    "status": "blocked",
    "message": f"Git guardrail failed: {reason}",
    "outcome": "guardrail_failed",
    "next_action": "fix_git_state",
    "requires_approval": False,
}
```

Guardrails must only run when NOT in dry_run mode and NOT in simulate mode.

`simulate_backlog()` must NOT call guardrails — simulation must always be safe to run.

### cli.py

Must support a `--skip-guardrails` flag for testing purposes only.

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

When no pending task:
- `task_name == "none"`
- `status == "no_task"`
- `message == "No pending tasks available."`

When execution fails:
- `status == "failed"`
- `outcome == "repair_required"`

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

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- calling guardrails inside `simulate_backlog`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_git_guardrails.py` must cover:

- running on `main` branch is blocked
- dirty worktree is blocked
- valid branch passes
- simulation mode bypasses all guardrails

`ruff check .` must pass. `pytest -q` must be fully green.
