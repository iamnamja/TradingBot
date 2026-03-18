# Task 037 — Persistent Backlog State

## Goal

Persist task execution state between orchestrator runs so the orchestrator can resume from where it left off without re-executing completed tasks.

## Why

Currently the orchestrator discovers tasks fresh each run. With persistent state, completed and failed tasks are remembered across restarts. Simulation mode must never modify real persistent state.

## Critical compatibility requirement

This task is a persistence-layer extension only.

Do not rewrite legacy orchestrator behavior.

The purpose of this task is to add persistent backlog state support while preserving all existing runner, dry-run, no-task, review, simulation, guardrail, and execute-task contracts unless persistent state explicitly requires a small additive change.

A solution is invalid if it changes the observable behavior of existing orchestrator tests unrelated to persistent state.

All existing public APIs must remain backward compatible:
- `OrchestratorRunner.__init__` signature unchanged
- `run_next_task(dry_run=False)` signature unchanged
- `simulate_backlog()` signature and return contract unchanged
- `BacklogTracker` existing interface unchanged

All existing passing tests must continue to pass.

## CRITICAL — existing runner semantics are locked

This task is NOT allowed to change any pre-existing runner behavior except to add persistence hooks.

A solution is invalid if any of the following existing tests would need their expected values changed:

- approval flow tests
- dry-run tests
- execute workflow tests
- full simulation tests
- git guardrail tests
- real execution tests
- real review gate tests
- generic runner tests

The implementation must preserve all existing return dictionaries and message strings exactly unless persistence strictly requires an additive hook.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `src/builder/orchestrator/backlog.py`
- `src/builder/orchestrator/state.py`
- `tests/test_orchestrator_persistent_backlog_state.py`

All three listed files must be materially updated in the same bundle.

## HARD FAIL RULE — bundle must be rejected if runner.py is included

If the bundle includes `src/builder/orchestrator/runner.py` at all, the solution is invalid.

This task must be completed by updating only:
- `src/builder/orchestrator/backlog.py`
- `src/builder/orchestrator/state.py`
- `tests/test_orchestrator_persistent_backlog_state.py`

Do not include `runner.py` in the bundle.
Do not modify `runner.py`.
Do not propose a rewritten `runner.py`.

## CRITICAL — runner.py is protected and must NOT be included as a deliverable

`src/builder/orchestrator/runner.py` is a stable, fully-tested file. Do NOT include it in the bundle.
Do NOT rewrite it. Do NOT modify it. Do NOT include it as a deliverable.

If this task requires new functionality in runner.py, add ONLY the smallest surgical changes required for persistence integration.
All existing methods must remain behaviorally unchanged except for the minimal persistence hooks explicitly required below.

The agent must NOT regenerate runner.py from scratch under any circumstances.

## Clarification — surgical runner edits are allowed but runner.py is still not a deliverable

`src/builder/orchestrator/runner.py` may be edited only if strictly necessary for persistence integration.

However:
- it must NOT be listed or treated as a primary deliverable for this task
- it must NOT be regenerated wholesale
- it must NOT be materially rewritten
- only the smallest possible persistence hooks are allowed

A valid solution may include a minimal patch to `runner.py`, but the main substantive work for this task must be in:
- `src/builder/orchestrator/backlog.py`
- `src/builder/orchestrator/state.py`
- `tests/test_orchestrator_persistent_backlog_state.py`

## Protected files / minimal change rule

`src/builder/orchestrator/runner.py` may be updated only surgically to:
- read persistent state
- write persistent state after task state transitions
- respect configurable state file path
- ensure simulation does not persist state

Do not rewrite unrelated runner semantics.

In particular, do not change:
- dry-run return keys and values
- no-task return keys and values
- legacy success message / status
- simulation final_status contract
- guardrail blocked outcome contract
- execute_task legacy default behavior
- review gate behavior outside what is strictly required for persistence

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

State is persisted to `tasks/state.json` by default, configurable via `ProjectConfig.state_path`.

State file path comes from:

```python
getattr(self.config, "state_path", "tasks/state.json")
```

Do not assume `state_path` exists.

## Task states

Valid state values:
- `pending` — not yet started
- `running` — currently executing
- `completed` — finished successfully
- `blocked` — waiting for approval
- `failed` — execution failed

## Required behavior

### `state.py` additions

`OrchestratorState` must support:

```python
def save(self, path: str) -> None:
    """Persist state to JSON file."""

@classmethod
def load(cls, path: str) -> "OrchestratorState":
    """Load state from JSON file. Returns empty state if file missing."""
```

The state file must be valid JSON at all times.

Missing file must yield an empty state, not an exception.

`state.py` must be materially updated in this task.
A solution is invalid if `state.py` is unchanged or only cosmetically changed.

### `backlog.py` additions

`BacklogTracker` must support:

```python
def load_state(self, state_path: str):
    """Load persisted task state."""

def save_state(self, state_path: str, tasks) -> None:
    """Persist task state."""

def update_task_status(self, task_name: str, status: str, state_path: str) -> None:
    """Update a task's status in persistent state."""
```

`BacklogTracker` must preserve existing scanning behavior and add only the persistence helpers needed by tests.

Do not remove existing task scanning semantics.
Do not rename task names in a way that breaks existing tests.

### `runner.py` integration

`run_next_task()` must:
1. Load existing state on startup via `read_backlog()`
2. Skip tasks with status `completed` when selecting next task
3. Save updated state after each task execution via `write_state()`
4. Mark task as `completed` on success, `failed` on failure

`simulate_backlog()` must NOT write to persistent state — simulation is read-only.

It may read state if needed for consistency, but it must not create or modify the state file.

## Locked runner contracts

The following must remain EXACTLY unchanged:

### `run_next_task(dry_run=True)` when a pending task exists

```python
{
    "dry_run": True,
    "task_name": "001_task.py",
    "status": "planned",
    "message": "Task is planned for execution.",
    "outcome": "noop",
    "next_action": "none",
    "requires_approval": False,
}
```

### `run_next_task()` when no pending task exists

```python
{
    "task_name": "none",
    "status": "no_task",
    "message": "No pending tasks available.",
    "outcome": "noop",
    "next_action": "none",
    "requires_approval": False,
}
```

### legacy success path

```python
{
    "task_name": "001_task.py",
    "status": "running",
    "message": "Task is now running.",
    "outcome": "ready_for_pr",
    "next_action": "merge",
    "requires_approval": False,
}
```

### review-blocked path

```python
{
    "task_name": "001_task.py",
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",
    "requires_approval": True,
}
```

### failure path

```python
{
    "task_name": "001_task.py",
    "status": "failed",
    "message": "Execution failed: Execution failed",
    "outcome": "repair_required",
    "next_action": "require_human_review",
}
```

### successful simulation

```python
{
    "processed_tasks": ["001_task.py", "002_task.py"],
    "stopped_reason": "",
    "final_status": "completed",
    "approval_required": False,
    "planned_actions": [
        "Task 001_task.py completed successfully.",
        "Task 002_task.py completed successfully.",
    ],
}
```

### approval-blocked simulation

```python
{
    "processed_tasks": ["001_task.py", "002_task.py"],
    "stopped_reason": "Approval required",
    "final_status": "blocked",
    "approval_required": True,
}
```

### failure simulation

```python
{
    "processed_tasks": ["001_task.py"],
    "stopped_reason": "Execution failed",
    "final_status": "failed",
    "approval_required": False,
    "planned_actions": [],
}
```

### guardrail-blocked path

- `status == "blocked"`
- `outcome == "guardrail_failed"`
- `task_name == "none"` for the blocked pre-execution guardrail case

## CRITICAL — `simulate_backlog` must remain behaviorally unchanged except for persistence read-only rules

Simulation must not call `write_state()` or modify any state file.

It must preserve the existing contract:
- `processed_tasks`
- `stopped_reason`
- `final_status`
- `approval_required`
- `planned_actions`

When backlog completes normally:
- `stopped_reason == ""`

Only non-empty stopped reasons allowed:
- `"Execution failed"`
- `"Approval required"`

## CRITICAL — `run_review` behavior

When `changed_files` is empty on the legacy/mock success path, return `{"mergeable": True}`.

Do not tighten review behavior in this task.

## CRITICAL — `ProjectConfig` must remain mutable

Do NOT use `@dataclass(frozen=True)` on `ProjectConfig` or any subclass.

Use `getattr(self.config, "state_path", "tasks/state.json")` everywhere — do not assume the field exists.

## Exact forbidden patterns

- writing state inside `simulate_backlog`
- changing `final_status` success value from `"completed"` to `"success"`
- returning `status == "blocked"` for the no-task path
- removing `dry_run` from dry-run results
- changing legacy success message away from `"Task is now running."`
- rewriting `execute_task()` so the default path returns a different contract
- omitting `BacklogTracker.save_state(...)`
- changing task naming semantics in a way that breaks existing runner tests
- rewriting large portions of `runner.py` unrelated to persistence
- calling `self.select_next_task()` or `scan_tasks()` inside `simulate_backlog` loop if existing behavior uses `get_next_task`
- `@dataclass(frozen=True)` on any config class
- assuming `state_path` exists on config without `getattr`
- leaving state file in corrupt or partial state on error
- unused local variables that ruff will flag
- treating `runner.py` as the main implementation surface for this task
- making `runner.py` the dominant source of line changes in the bundle

## Explicitly invalid changes

INVALID:
- returning `blocked` on legacy success path
- changing dry-run message to include the task name
- removing `next_action` from the no-task path
- changing simulation `planned_actions` from `list[str]` to `list[dict]`
- stopping approval simulation after only `["001_task.py"]`
- changing `execute_task()` return shape for existing real-execution tests
- changing `execute_task()` default mock `changed_files`
- changing guardrail-blocked `task_name`
- changing any existing expected message string
- changing any existing expected status string
- regenerating `runner.py` wholesale

## HARD FAIL RULE — tests must import TaskStatus when used

If any test file constructs `TaskStatus(...)`, it must explicitly import `TaskStatus` from `builder.orchestrator.state`.

Using `status="pending"` directly in `TaskMetadata(...)` is invalid unless the existing code explicitly supports that constructor shape.

## HARD FAIL RULE — no placeholder implementations

The following are invalid anywhere in the bundle:
- `pass` in `execute_task`
- `pass` in `process_execution_result`
- placeholder comments like "Execution logic here"
- replacing existing production logic with stubs

## Acceptance criteria

Tests in `tests/test_orchestrator_persistent_backlog_state.py` must cover:

- completed tasks are skipped on next run
- failed tasks are recorded in state
- state file is created if missing
- simulation does not modify state
- state persists correctly across two sequential `run_next_task()` calls

And all pre-existing orchestrator tests must remain green.

`ruff check .` must pass. `pytest -q` must be fully green.

## CRITICAL — `process_execution_result` must remain behaviorally unchanged

Do NOT simplify `process_execution_result`. Route through `FailureClassifier`, `RepairWorkflow`, and audit log calls.

### Review blocked path must return exactly:

```python
{
    "task_name": task.name,
    "status": "running",
    "message": "Task is now running.",
    "outcome": "review_blocked",
    "next_action": "requires_approval",
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
    "next_action": next_action,
    "requires_approval": repair_action.get("requires_approval", True),
}
```

Do NOT return `"Task execution failed."` or any other message format.
Do NOT return `requires_approval: False` on the failure path.
Do NOT skip `FailureClassifier` or `RepairWorkflow`.

### Required imports in `runner.py` — do not remove any:

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

## CRITICAL — `run_next_task` normalization

Must still call `normalize_execution_result` between `execute_task` and `process_execution_result`:

```python
execution_result = self.execute_task(running_task)
normalized_result = normalize_execution_result(execution_result)
return self.process_execution_result(normalized_result, running_task)
```

## CRITICAL — `execute_task` default mock return

When `task_runner_command` is `None`, return exactly:

```python
{
    "success": True,
    "output": "Task executed successfully",
    "changed_files": ["file1.py"],
}
```

Do NOT change that default return in this task.

## CRITICAL — Test import paths

All test imports must use `from builder.orchestrator...` NOT `from src.builder.orchestrator...`.

Correct:

```python
from builder.orchestrator.runner import OrchestratorRunner
```

Invalid:

```python
from src.builder.orchestrator.runner import OrchestratorRunner
```

## CRITICAL — `state.py` must be materially updated

`state.py` must not remain a minimal persistence wrapper only.

It must be materially updated in a way that is central to this task, for example:
- robust JSON serialization and deserialization helpers
- stable task-state round-tripping
- explicit missing-file behavior
- explicit corrupted-file recovery behavior
- helper logic that is meaningfully exercised by the persistence tests

A cosmetic or trivially small change to `state.py` is invalid.

## Minimal runner-change guidance

If runner changes are required, they must be surgical and additive only.

Acceptable examples:
- adding a small helper for state path resolution
- reading persisted state before selecting the next task
- writing state after status transitions
- ensuring simulation remains read-only

Unacceptable examples:
- rewriting `run_next_task()` return shapes
- changing no-task / dry-run / success / failure / blocked semantics
- changing simulation return semantics unrelated to persistence
- changing guardrail outcome semantics
- changing default execute-task behavior

## Suggested implementation shape

A valid implementation will likely:
- add `save/load` logic in `state.py`
- add `save_state/load_state/update_task_status` helpers in `backlog.py`
- make only the smallest possible integration hooks in `runner.py`
- leave all unrelated contracts untouched
