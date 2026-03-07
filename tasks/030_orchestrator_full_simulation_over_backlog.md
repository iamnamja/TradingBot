# Task 030: Orchestrator full simulation over backlog

## Goal
Add a higher-level simulation mode that can walk across multiple tasks in backlog order without mutating repo or remote state.

This task should prove the orchestrator can reason across a backlog, not just a single task.

## Deliverables
- updates to:
  - `src/builder/orchestrator/runner.py`
  - `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_full_simulation.py`

## Existing repo dependencies (NOT deliverables)
Reuse existing orchestrator modules and dry-run capabilities.
Do not create a parallel orchestration stack.

## Scope
This task is for **simulation over multiple tasks**, not full autonomous live execution.

## Required behavior

### Simulation mode
The orchestrator should be able to:
- iterate over tasks in backlog order
- simulate what would happen for each task
- stop when a blocking or approval-required condition is encountered
- return a structured simulation summary

### Summary contract
This is the most important rule in the task.

The simulation summary must use deterministic primitive values only.

Required fields:
- `processed_tasks: list[str]`
- `stopped_reason: str`
- `final_status: str`

Optional:
- `approval_required: bool`
- `planned_actions: list[str]`

### Stop conditions
Simulation should stop when:
- no more pending tasks exist
- an approval-required checkpoint is reached
- a blocking policy/review outcome is reached
- a failure classification indicates human review is required

### Mutation boundary
Simulation mode must not:
- create branches
- push
- create PRs
- merge PRs
- write remote state

Tests should verify the mutation boundary through injected collaborators.

### Test guidance
Tests must cover at least:
- empty backlog
- multiple successful planned tasks
- stop on approval-required checkpoint
- stop on blocking condition

Do not assert on mock repr strings.
Do not require live git/GitHub access.

## Portability requirement
Do not hardcode TradingBot-specific task names or assumptions.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- simulation walks backlog deterministically
- simulation stops correctly on blocking conditions
- mutation boundary is preserved
