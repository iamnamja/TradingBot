# Task 036 — Resume After Approval

## Goal

Allow the orchestrator to resume execution after a human-approval checkpoint has been granted.

## Why

When the orchestrator encounters a review-blocked task requiring approval, it stops and waits. Once approval is granted (externally), the orchestrator must be able to resume from exactly that checkpoint rather than restarting from scratch.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- `approval.py` existing `create_approval_checkpoint` function signature unchanged

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/approval.py`
- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_resume_after_approval.py`

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

### approval.py additions

Must add to existing `approval.py` (without removing `create_approval_checkpoint`):

```python
def load_approval_checkpoint(state_path: str) -> dict | None:
    """Load the most recent pending approval checkpoint. Returns None if none exists."""

def grant_approval(state_path: str, task_name: str) -> bool:
    """Mark an approval checkpoint as granted. Returns True if successful."""

def is_approval_granted(checkpoint: dict) -> bool:
    """Returns True if the checkpoint status is 'approved'."""
```

### runner.py

Must add `resume_from_approval()` method:

```python
def resume_from_approval(self) -> dict[str, Any]:
    """
    Resume execution from the latest approved checkpoint.
    Returns a result dict with task_name, status, message, outcome.
    Fails with status='blocked' if no approved checkpoint exists.
    """
```

### cli.py

Must add `--resume` flag:

```
py agents/run_task.py --resume
```

When `--resume` is passed, calls `runner.resume_from_approval()` instead of `run_next_task()`.

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

- removing or changing `create_approval_checkpoint` signature
- adding required parameters to `run_next_task`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_resume_after_approval.py` must cover:

- resume succeeds when approval checkpoint is granted
- resume fails when no checkpoint exists
- resume fails when checkpoint is not yet approved
- `--resume` CLI flag triggers resume path

`ruff check .` must pass. `pytest -q` must be fully green.
