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

## runner.py policy

`src/builder/orchestrator/runner.py` is NOT a primary deliverable for this task.

However, this task is allowed to include a **small surgical patch** to `runner.py` if needed for persistence integration.

Allowed runner changes:
- add / use a helper like `_state_file_path()`
- read persisted state before selecting the next task
- write persisted state after successful or failed task execution
- ensure sequential runs and fresh runner instances see persisted completed/failed tasks
- ensure simulation does not write state

Forbidden runner changes:
- wholesale rewrite or regeneration of `runner.py`
- changing dry-run / no-task / success / failure / blocked return contracts
- changing guardrail semantics
- changing default `execute_task()` mock behavior
- changing simulation return schema
- removing existing audit / repair / normalization flow

A solution is invalid if `runner.py` is rewritten wholesale.

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

The bundle may additionally include:
- `src/builder/orchestrator/runner.py`

But only if it is surgically modified for persistence integration.

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

Current failure pattern to fix:
- persistence helpers may exist, but state is not wired into the real runner flow strongly enough
- new tests must not be written in a way that breaks existing `state.py` / `backlog.py` equality contracts
- the fix must include only the smallest persistence hook needed so completed tasks are actually skipped on later runs and the state file is actually created after real execution
- new persistence tests must use a real config object with `state_path` set, not undefined locals or raw dict config
- failed-task tests must explicitly patch execution to fail; success-path tests must not assert failed state by default
- new persistence tests must not use mocked config objects that make guardrail patterns non-string values
- persistence tests should bypass guardrails safely so they test persistence, not git state
- current failing persistence tests are still tripping guardrails before state is written; fix the tests/config so persistence logic actually runs

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

## HARD FAIL RULE — state serialization must be explicit and JSON-safe

The following are invalid in `state.py` or `backlog.py`:
- `json.dump([task.__dict__ for task in ...], ...)`
- relying on dataclass `__dict__` for persistence
- writing nested `TaskStatus` objects directly to JSON

State must serialize each task explicitly in JSON-safe form, e.g.:
- `name: str`
- `order: int`
- `status: str`

On load, `status: str` must be converted back into `TaskStatus(status=...)`.

`backlog.py` helpers must also satisfy these behaviors:
- `load_state(state_path)` returns `[]` if the file does not exist
- `load_state(state_path)` never raises `FileNotFoundError` for a missing state file
- `save_state(state_path, tasks)` creates the parent directory if needed
- `update_task_status(task_name, status, state_path)` loads the current persisted tasks, updates the matching task if present, and saves the full updated task list
- `update_task_status(...)` must not reference undefined locals like `tasks`

## HARD FAIL RULE — no frozen dataclasses in persistence models

Do NOT use `@dataclass(frozen=True)` on:
- `TaskStatus`
- `TaskMetadata`
- `OrchestratorState`

## HARD FAIL RULE — no ruff violations in the persistence test file

`tests/test_orchestrator_persistent_backlog_state.py` must not contain:
- unused locals
- unused imports
- placeholder variables created only for comments

## HARD FAIL RULE — persistence tests must verify real runner-backed behavior

The persistence tests must verify behavior by exercising the real runner flow, not by only testing serialization helpers in isolation.

At minimum they must verify:
- a state file is created after a real `run_next_task(dry_run=False)` run
- completed tasks are skipped on the next run
- failed tasks are recorded in persisted state after a real failed run
- a fresh runner instance picks up persisted state from a previous run

If the tests only validate `save_state()` / `load_state()` helpers and do not verify real runner-backed persistence behavior, the solution is invalid.

## HARD FAIL RULE — do not fake persistence tests by patching runner entrypoints

The following are invalid in `tests/test_orchestrator_persistent_backlog_state.py`:
- patching `OrchestratorRunner.run_next_task`
- patching `OrchestratorRunner.simulate_backlog`
- asserting persistence behavior after only calling `save_state()` manually
- asserting failed-task persistence without a real `run_next_task(dry_run=False)` invocation that is explicitly forced to fail via `runner.execute_task`

Persistence tests must exercise the real runner flow.

Acceptable pattern for a failed-task persistence test:
```python
runner = OrchestratorRunner(...)
runner.skip_guardrails = True
runner.execute_task = lambda task: {"success": False, "failure_text": "Execution failed"}
result = runner.run_next_task(dry_run=False)
state = OrchestratorState.load(config.state_path)
```

Acceptable pattern for a successful persistence test:
```python
runner = OrchestratorRunner(...)
runner.skip_guardrails = True
result = runner.run_next_task(dry_run=False)
state = OrchestratorState.load(config.state_path)
```

## HARD FAIL RULE — state file creation and task skipping require real runner wiring

A solution is invalid if it only updates `backlog.py` and `state.py` but does not wire persistence into `runner.py` enough to make these behaviors true:
- `run_next_task(dry_run=False)` creates the state file when it did not already exist
- after a successful first run, a second `run_next_task(dry_run=False)` does NOT execute the same completed task again
- a new `OrchestratorRunner` instance created later reads the persisted state and skips already-completed tasks
- failed runs are persisted with status `failed`

If those behaviors are not implemented through real runner-backed persistence hooks, the solution is invalid.

`runner.py` must therefore include the minimal persistence integration needed so that:
- `read_backlog()` or equivalent can tolerate a missing state file
- `run_next_task(dry_run=False)` writes state after success and failure transitions
- `run_next_task(dry_run=True)` preserves existing dry-run contract and does not create state
- `simulate_backlog()` remains read-only and does not persist state

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

## HARD FAIL RULE — preserve existing state-model equality semantics

Do NOT replace existing equality-friendly task/state models with plain classes that rely on object identity.

A solution is invalid if it rewrites `TaskStatus`, `TaskMetadata`, or `OrchestratorState` into manual classes that break existing equality-based tests such as:

```python
assert tasks[0] == TaskMetadata(name="task_one.py", order=1, status=TaskStatus(status="pending"))
```

`state.py` must preserve or implement value-based equality semantics compatible with existing backlog tests.

If dataclasses are already used in the existing codebase for these models, keep that approach.
Do NOT regress them into plain classes without `__eq__`.

## HARD FAIL RULE — do not regress existing state/backlog test contracts

This task must keep existing backlog/state tests green.

A solution is invalid if it breaks any of these behaviors:
- `scan_tasks()` still returns equality-comparable `TaskMetadata` values
- `get_next_task()` still returns equality-comparable `TaskMetadata` values
- `load_state()` round-trips persisted tasks into equality-comparable `TaskMetadata` values
- `TaskStatus(status="pending")` remains a valid constructor shape
- `TaskMetadata(name=..., order=..., status=TaskStatus(...))` remains a valid constructor shape

## HARD FAIL RULE — preserve dataclass/value semantics in state.py

If the existing code uses dataclasses for `TaskStatus`, `TaskMetadata`, or `OrchestratorState`, keep them as dataclasses.

Do NOT convert them into plain classes unless you fully preserve value-based equality and constructor compatibility.

The following regressions are invalid:
- equality failures in existing backlog tests
- constructor shape changes that break `TaskStatus(status="pending")`
- constructor shape changes that break `TaskMetadata(name=..., order=..., status=TaskStatus(...))`

## HARD FAIL RULE — persistence tests must set real state_path on config

If persistence tests use `ProjectAdapter.get_tradingbot_default_config()`, they must explicitly set:

```python
config.tasks_directory = str(tasks_dir)
config.state_path = str(tasks_dir / "state.json")
```

Do NOT create unused `state_file` locals.
Do NOT reference undefined fixtures like `tmp_path` inside another fixture unless it is explicitly passed in.

## HARD FAIL RULE — persistence tests must distinguish success vs failure explicitly

If a persistence test expects a failed task to be recorded, it must explicitly monkeypatch or stub execution so the run actually fails.

It is invalid to call the default `run_next_task(dry_run=False)` path and then assert a failed status without forcing failure.

Likewise, if a test expects a completed task, it must use the default success path or an explicit success stub.

## HARD FAIL RULE — new persistence tests must not conflict with existing runner defaults

Remember that default `execute_task()` mock behavior returns success when `task_runner_command` is `None`.

A solution is invalid if new persistence tests assume failure without explicitly patching `execute_task`.

## HARD FAIL RULE — persistence tests must use the real config shape expected by runner

Do NOT instantiate `OrchestratorRunner` in persistence tests with a raw dict config like:

```python
OrchestratorRunner(config={"tasks_directory": ...}, ...)
```

Use the real project config shape already expected by production code, e.g.:
- `ProjectAdapter.get_tradingbot_default_config()` and then override `tasks_directory` / `state_path`
- or a real `ProjectConfig(...)` instance

A solution is invalid if new persistence tests require changing `runner.__init__` to accept raw dict config.

## HARD FAIL RULE — do not use MagicMock config objects in persistence tests

Do NOT patch `ProjectAdapter.get_tradingbot_default_config()` to return a `MagicMock` or mocked config object for persistence tests.

Use a real mutable config object instead, for example:
- `config = ProjectAdapter.get_tradingbot_default_config()`
- then set `config.tasks_directory = ...`
- then set `config.state_path = ...`

A solution is invalid if persistence tests create a mocked config whose fields like:
- `branch_naming_pattern`
- `protected_file_patterns`
- `approval_required_file_patterns`

become `MagicMock` values and break guardrail code.

## HARD FAIL RULE — persistence tests must bypass guardrails safely without changing runner contracts

Persistence tests that exercise real `run_next_task(dry_run=False)` behavior must avoid unrelated git guardrail failures.

Acceptable approaches:
- set `runner.skip_guardrails = True` in the persistence tests after constructing the runner
- or configure a real config object with a valid string `branch_naming_pattern` and clean guardrail-compatible values

Do NOT change production guardrail behavior to satisfy persistence tests.

A solution is invalid if it changes production guardrail semantics instead of configuring tests correctly.

For this task, prefer the simplest safe approach:
- after constructing the real runner in persistence tests, set `runner.skip_guardrails = True`

This avoids unrelated git environment failures and ensures the tests exercise persistence behavior rather than guardrail behavior.

A solution is invalid if persistence tests call real `run_next_task(dry_run=False)` without either:
- `runner.skip_guardrails = True`, or
- a fully real guardrail-compatible git/config setup.

## HARD FAIL RULE — persistence tests must create real task files before calling run_next_task

Any persistence test that expects `run_next_task(dry_run=False)` to create state or advance tasks must first create real task files in the test tasks directory.

It is invalid to call `run_next_task()` against an empty task directory and then assert that state was created for executed work.

## HARD FAIL RULE — persistence test fixtures must create the tasks directory before writing files

If a fixture returns a tasks directory path like `tmp_path / "tasks"`, it must ensure the directory actually exists before any test writes files into it, for example with:

```python
tasks_dir = tmp_path / "tasks"
tasks_dir.mkdir(parents=True, exist_ok=True)
return tasks_dir
```

A solution is invalid if persistence tests attempt to open files under a tasks directory that was never created.

## HARD FAIL RULE — required imports must be present in touched files

If `state.py` uses `os.path.exists`, it must import `os`.

If tests construct or compare `TaskMetadata`, they must import `TaskMetadata`.

If tests use `os.path` or other `os` functions, they must import `os`.

A solution is invalid if it introduces obvious undefined-name lint failures such as:
- missing `os` import in `state.py`
- missing `TaskMetadata` import in persistence tests
- undefined fixture variables such as `tmp_path`

## HARD FAIL RULE — persistence tests must respect existing task-name normalization

Do NOT change production task-name normalization semantics in `BacklogTracker`.

If task files are created in tests, choose filenames whose normalized names remain distinct after stripping the numeric prefix, for example:
- `001_first.py`
- `002_second.py`

Do NOT force production code changes just to preserve full prefixed filenames in new persistence tests.

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

The persistence tests must also:
- import every symbol they use (`TaskMetadata`, `TaskStatus`, etc.)
- avoid unused locals that ruff will reject
- use real task filenames that normalize to distinct task names
- construct runner config using the real config object shape already used by production code
- create the tasks directory fixture before writing any task files into it
- set `config.state_path` explicitly to a valid file path under the created tasks directory
- avoid duplicate test method names
- use a real config object, not a patched `MagicMock` config
- set `runner.skip_guardrails = True` in persistence tests unless the test is explicitly about guardrails
- assert persistence results only after the runner has actually executed past guardrails
- not rely on git guardrails to be satisfied in the test environment

- not patch `run_next_task` or `simulate_backlog`
- force failure by patching only `runner.execute_task`, not the higher-level runner entrypoint
- verify that `state.py` was materially updated, not merely re-exported or cosmetically changed

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

A solution is invalid if `state.py` is effectively unchanged while persistence behavior is pushed entirely into `backlog.py` or tests.

`state.py` should own meaningful persistence logic, such as:
- `OrchestratorState.save(...)`
- `OrchestratorState.load(...)`
- explicit task-to-dict / dict-to-task conversion helpers

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
