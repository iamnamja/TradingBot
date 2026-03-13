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

- `src/builder/orchestrator/runner.py`
- `src/builder/orchestrator/backlog.py`
- `src/builder/orchestrator/state.py`
- `tests/test_orchestrator_persistent_backlog_state.py`

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
