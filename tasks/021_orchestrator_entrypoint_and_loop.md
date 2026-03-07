# Task 021: Orchestrator entrypoint and loop runner

## Goal
Create the first operational orchestrator entrypoint that wires together the existing orchestrator components into a single loop.

## Deliverables
- `src/builder/orchestrator/runner.py`
  - `class OrchestratorRunner`
  - method(s) to:
    - load project config
    - read backlog/state
    - select next task
    - invoke the next-step flow

- `src/builder/orchestrator/cli.py`
  - `main() -> int`
  - a simple command-line entrypoint for the orchestrator

- `tests/test_orchestrator_runner.py`

## Existing repo dependencies (NOT deliverables)
Reuse existing orchestrator modules rather than recreating them:
- state/backlog
- review checker
- failure classifier
- merge manager
- repair workflow
- project adapter/config

Do not recreate those modules unless modification is truly required.

## Scope
This task is about wiring the loop together.
For v1, it is acceptable if the loop only executes a **single next-task cycle** rather than running forever.

## Required behavior

### Constructor contract
`OrchestratorRunner` should accept enough constructor dependencies to be testable.

At minimum, it must support:
- a project config or project adapter
- a backlog tracker
- an initial orchestrator state

If the first argument is a plain `ProjectConfig`, the runner must use it directly.

If the first argument is an adapter object, the runner may read config from that adapter.

Do **not** assume the first argument always has `.config`.

### Backlog source of truth
For v1, task selection should use the backlog tracker's task discovery method rather than relying only on persisted state.

Normative rule:
- `select_next_task()` should use the backlog tracker's task list / scan result
- if no tasks are found there, it may fall back to state
- tests may monkeypatch the backlog tracker discovery method

This is the most important behavioral rule for this task.

### State handling
If `OrchestratorState` is immutable/frozen, tests and runner behavior must still work cleanly.
Acceptable patterns:
- replace the whole state object instead of mutating frozen fields
- or use non-frozen state models if that is already the project convention

Tests must not rely on mutating a frozen dataclass field in place.

### Task identity
The runner should work with real task objects from the backlog/state layer.
Do not rely on raw `MagicMock.name` semantics for task identity.

Use explicit task fields such as:
- `name`
- `path`
- `order`
- `status`

### Orchestrator flow
The runner must:
- load project config/adapter
- read backlog/state
- determine the next pending task
- return or record what task would run next

### Loop shape
For v1, one cycle is enough:
- select next task
- record state transition for that task as running
- stop after that point or return a structured decision object

This task does **not** need to execute the full dev-agent workflow yet if that would overextend scope.

### Return shape
`run_next_task()` should return a structured result with deterministic primitive fields.

Suggested fields:
- `task_name: str`
- `status: str`
- `message: str`

If no pending task exists, return a deterministic no-op result such as:
- `task_name = "none"`

## Test guidance

### Avoid brittle mocks
Tests should prefer simple fake task objects or real state/task dataclasses rather than loose MagicMocks for core task identity.

### Normative examples
Example 1:
- backlog tracker discovery returns one pending task named `001_task.py`
- `select_next_task()` returns that exact task object

Example 2:
- `run_next_task()` returns a dict whose `task_name` is `001_task.py`

Example 3:
- if no pending tasks exist, runner returns a deterministic no-op result rather than failing

### CLI
Provide a simple CLI entrypoint that can:
- run one orchestrator cycle
- print a concise summary
- return success on happy path

## Portability requirement
Do not hardcode TradingBot-specific task names in the engine.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- runner can select and mark the next task deterministically
- tests do not depend on mutating frozen dataclass fields
- tests do not depend on `MagicMock.name` identity behavior
- tests can pass either a `ProjectConfig` or adapter-compatible object without attribute errors
- selection behavior follows the backlog discovery rule above
- CLI returns success on happy path
