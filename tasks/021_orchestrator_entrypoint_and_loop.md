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

### CLI
Provide a simple CLI entrypoint that can:
- run one orchestrator cycle
- print a concise summary

## Portability requirement
Do not hardcode TradingBot-specific task names in the engine.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- runner can select and mark the next task deterministically
- CLI returns success on happy path
