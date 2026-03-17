# Task 037 — Persistent Backlog State

## Goal

Persist task execution state between orchestrator runs so the orchestrator can resume from where it left off without re-executing completed tasks.

## Why

Currently the orchestrator discovers tasks fresh each run. With persistent state, completed and failed tasks are remembered across restarts. Simulation mode must never modify real persistent state.

## Critical compatibility requirement

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- `BacklogTracker` existing interface unchanged

All existing passing tests must continue to pass.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/backlog.py`
- `src/builder/orchestrator/state.py`
- `tests/test_orchestrator_persistent_backlog_state.py`

All four files must be materially updated in the same bundle.


## CRITICAL — runner.py is PROTECTED and must NOT be included as a deliverable

`src/builder/orchestrator/runner.py` is a stable, fully-tested file. Do NOT include it in the bundle.
Do NOT rewrite it. Do NOT modify it. Do NOT include it as a deliverable.

If this task requires new functionality in runner.py, add ONLY the specific new method described,
using surgical `str_replace`-style additions. All existing methods must remain exactly unchanged.

The agent must NOT regenerate runner.py from scratch under any circumstances.

## Bundle completeness requirement

The bundle is incomplete unless all listed deliverables are present.

## Critical anti-truncation rule

`src/builder/orchestrator/runner.py` must visibly contain all of these method headers:

- `def select_next_task(`
- `def run_next_task(`
- `def execute_task(`
- `def process_execution_result(`
- `def simulate_backlog(`

And must contain a `simulate_backlog` return dict with all five keys:
`processed_tasks`, `stopped_reason`, `final_status`, `approval_required`, `planned_actions`

## State file

State is persisted to `tasks/state.json` by default (configurable via `ProjectConfig.state_path`).

## Task states

Valid state values:
- `pending` — not yet started
- `running` — currently executing
- `completed` — finished successfully
- `blocked` — waiting for approval
- `failed` — execution failed

## Required behavior

### state.py additions

`OrchestratorState` must support:

```python
def save(self, path: str) -> None:
    """Persist state to JSON file."""

@classmethod
def load(cls, path: str) -> "OrchestratorState":
    """Load state from JSON file. Returns empty state if file missing."""
```

### backlog.py additions

`BacklogTracker` must support:

```python
def update_task_status(self, task_name: str, status: str, state_path: str) -> None:
    """Update a task's status in persistent state."""
```

### runner.py integration

`run_next_task()` must:
1. Load existing state on startup via `read_backlog()`
2. Skip tasks with status `completed` when selecting next task
3. Save updated state after each task execution via `write_state()`
4. Mark task as `completed` on success, `failed` on failure

`simulate_backlog()` must NOT write to persistent state — simulation is read-only.

### Exact state persistence rules

- State file path comes from `self.config.state_path` if present, otherwise defaults to `tasks/state.json`
- Use `getattr(self.config, "state_path", "tasks/state.json")` to avoid AttributeError
- State file is created if it does not exist
- State file is valid JSON at all times — never leave it in a partial/corrupt state

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
    normalized_result = normalize_execution_result(execution_result)
    result = self.process_execution_result(normalized_result, next_task)

    if result["status"] == "failed":
        stopped_reason = normalized_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

Simulation must not call `write_state()` or modify any state file.

## CRITICAL — run_review behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

## CRITICAL — ProjectConfig must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

Use `getattr(self.config, "state_path", "tasks/state.json")` everywhere — do not assume the field exists.

## Exact forbidden patterns

- writing state inside `simulate_backlog`
- `break` when `requires_approval` is True in `simulate_backlog`
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop
- `@dataclass(frozen=True)` on any config class
- assuming `state_path` exists on config without `getattr`
- leaving state file in corrupt/partial state on error
- unused local variables that ruff will flag

## Acceptance criteria

Tests in `tests/test_orchestrator_persistent_backlog_state.py` must cover:

- completed tasks are skipped on next run
- failed tasks are recorded in state
- state file is created if missing
- simulation does not modify state
- state persists correctly across two sequential `run_next_task()` calls

`ruff check .` must pass. `pytest -q` must be fully green.

## CRITICAL — process_execution_result must be implemented exactly

Do NOT simplify `process_execution_result`. Route through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Review blocked path must return exactly:
```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",   # NOT "review", "merge", or anything else
    "requires_approval": True,
}
```

### Failure path must return:
```python
{
    "task_name": task.name,
    "status": "failed",
    "message": f"Execution failed: {failure_text}" if failure_text else "Execution failed.",
    "outcome": "repair_required",
    "next_action": next_action,           # from repair_action, fallback "require_human_review"
    "requires_approval": repair_action.get("requires_approval", True),  # True by default
}
```

Do NOT return `"Task execution failed."` or any other message format.
Do NOT return `requires_approval: False` on the failure path.
Do NOT skip `FailureClassifier` or `RepairWorkflow`.

### Required imports in runner.py — do not remove any:
```python
from .approval import create_approval_checkpoint
from .audit import (
    log_approval_checkpoint,
    log_classification_result,
    log_repair_decision,
    log_review_verdict,
    log_selected_task,
)
from .execution_result import normalize_execution_result
from .failures import FailureClassifier
from .repair import RepairWorkflow
```

## CRITICAL — stopped_reason contract

When backlog completes normally: `stopped_reason == ""` (empty string). NEVER `"All tasks completed"` or any other non-empty value.

Only non-empty values allowed:
- `"Execution failed"` on task failure
- `"Approval required"` when approval is needed

## CRITICAL — simulate_backlog with normalization

Must call `normalize_execution_result` before `process_execution_result`:

```python
while True:
    next_task = self.backlog_tracker.get_next_task([])
    if not next_task:
        break

    processed_tasks.append(next_task.name)
    execution_result = self.execute_task(next_task)
    normalized_result = normalize_execution_result(execution_result)
    result = self.process_execution_result(normalized_result, next_task)

    if result["status"] == "failed":
        stopped_reason = normalized_result.get("failure_text", "Execution failed")
        final_status = "failed"
        break

    if result.get("requires_approval", False):
        approval_required = True
        stopped_reason = "Approval required"
        final_status = "blocked"
        continue  # MUST be continue, NOT break

    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

## CRITICAL — run_next_task normalization

Must call `normalize_execution_result` between `execute_task` and `process_execution_result`:

```python
execution_result = self.execute_task(running_task)
normalized_result = normalize_execution_result(execution_result)
return self.process_execution_result(normalized_result, running_task)
```

## CRITICAL — execute_task default mock return

When `task_runner_command` is None, return exactly:
```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": ["file1.py"],
}
```

Do NOT return `{"success": True, "changed_files": []}` — the empty list causes test failures.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.

Correct:
```python
from builder.orchestrator.runner import OrchestratorRunner
from builder.orchestrator.policy import PolicyEngine
```

Invalid (breaks CI):
```python
from src.builder.orchestrator.runner import OrchestratorRunner
```
