# Task 021: Orchestrator entrypoint and loop runner

## Goal
Create the first operational orchestrator entrypoint that wires together the existing orchestrator components into a single loop.

## Deliverables
- `src/builder/orchestrator/runner.py`
  - `class OrchestratorRunner`
  - method(s) to:
    - load project config
    - load backlog/state
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

### Construction and dependency injection
`OrchestratorRunner` should accept its collaborators via constructor injection where practical.
At minimum, it should be possible in tests to inject or override:
- project adapter/config
- backlog tracker
- initial orchestrator state

Do not hardwire all collaborators inside methods if that makes testing brittle.

### State handling
If `OrchestratorState` is an immutable/frozen dataclass, tests and runner behavior must still work cleanly.
Acceptable patterns:
- replace the whole state object instead of mutating frozen fields
- or use non-frozen state models if that is already the project convention

Tests must not rely on mutating a frozen dataclass field in place.

### Task shape assumptions
The runner should work with real task objects from the backlog/state layer.
Do not rely on raw `MagicMock.name` semantics for task identity.

Use explicit task fields such as:
- `task_id`
- `name`
- `path`
or whatever the real state model already provides.

### Orchestrator flow
The runner must:
- load project config/adapter
- read orchestrator state
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
Use plain strings / booleans / dicts, not MagicMock-dependent values.

Suggested fields:
- `task_name: str`
- `status: str`
- `message: str`

## Test guidance

### Avoid brittle mocks
Tests should prefer simple fake task objects or real state/task dataclasses rather than loose MagicMocks for core task identity.

### Normative examples
Example 1:
- state contains one pending task named `021_example`
- `select_next_task()` returns that exact task object

Example 2:
- `run_next_task()` returns a dict whose `task_name` is the real task name string, not a mock object

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
- CLI returns success on happy path
