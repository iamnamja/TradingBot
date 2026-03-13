# Task 035 — PR Creation Workflow

## Goal

Allow the orchestrator to create a GitHub PR after successful task execution that passes review and policy checks.

## Why

After execution succeeds and review passes, the orchestrator should automate PR creation rather than requiring manual intervention for every task.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged — do NOT add `create_pr=` parameter
- `simulate_backlog()` signature and return contract unchanged

PR creation must be opt-in and must not run in dry_run or simulate mode.

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/merge.py`
- `src/builder/orchestrator/command_runner.py`
- `tests/test_orchestrator_pr_creation_workflow.py`

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

### command_runner.py

Must define a `CommandRunner` class for executing shell commands safely:

```python
class CommandRunner:
    def run(self, cmd: list[str], capture: bool = True) -> dict[str, Any]: ...
```

Returns:
```python
{
    "success": bool,
    "stdout": str,
    "stderr": str,
    "returncode": int,
}
```

Must be mockable in tests — do not use subprocess directly in caller code.

### merge.py

Must define a `PRCreator` class:

```python
class PRCreator:
    def __init__(self, command_runner: CommandRunner) -> None: ...
    def create_pr(self, branch: str, title: str, body: str) -> dict[str, Any]: ...
```

`create_pr` must use `gh pr create` via `CommandRunner`.

Returns:
```python
{
    "pr_attempted": bool,
    "pr_success": bool,
    "pr_url": str,
    "error": str,
}
```

### runner.py integration

`run_next_task()` result must include:
```python
{
    "pr_attempted": bool,
    "pr_success": bool,
}
```

PR creation must only run when ALL of these are true:
- execution succeeded
- review is mergeable
- `requires_approval == False`
- `dry_run == False`

PR must NOT be attempted when:
- dry_run is True
- review is blocked
- approval is required

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

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

## Exact forbidden patterns

- adding `create_pr=` to `run_next_task` signature
- running PR creation in dry_run or simulate mode
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- calling `gh` CLI directly in runner — must go through `CommandRunner`
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_pr_creation_workflow.py` must cover:

- mergeable success path triggers PR creation
- review blocked does not trigger PR
- approval required does not trigger PR
- dry run does not trigger PR
- PR creation failure is handled gracefully

`ruff check .` must pass. `pytest -q` must be fully green.
