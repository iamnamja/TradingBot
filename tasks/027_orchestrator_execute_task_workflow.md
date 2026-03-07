# Task 027: Orchestrator execute-task workflow

## Goal
Wire the existing orchestrator components into a real single-task execution workflow.

This task should move the orchestrator from “can select a task” to “can run one task workflow end to end in a controlled way.”

## Deliverables
- updates to:
  - `src/builder/orchestrator/runner.py`
  - `src/builder/orchestrator/cli.py`
- `tests/test_orchestrator_execute_workflow.py`

## Existing repo dependencies (NOT deliverables)
Reuse existing orchestrator modules rather than recreating them:
- `state.py`
- `backlog.py`
- `review.py`
- `failures.py`
- `merge.py`
- `repair.py`
- `policy.py`
- `audit.py`
- `project_config.py`
- `project_adapter.py`

Do not recreate these modules unless a minimal modification is truly required.

## Scope
This task should implement a **single-task workflow**, not a forever loop.

That means:
- pick one next task
- execute the task workflow once
- return a structured result
- stop

## Required workflow
The workflow should do all of the following in order:

1. determine the next pending task
2. mark or represent the task as running
3. invoke the task execution step through an injected collaborator or command wrapper
4. inspect the result
5. if successful:
   - run review/compliance evaluation
   - apply policy
   - decide whether the result is mergeable or requires approval
6. if unsuccessful:
   - run failure classification
   - run repair decision logic
7. write audit events for major decisions
8. return a structured orchestration result

## Execution contract
This is the most important rule in the task.

The runner must **not** directly shell out to hardcoded commands inside business logic.
Instead, inject or wrap the execution step so tests can simulate:
- success
- failure
- review blocker
- approval-required outcome

Acceptable patterns:
- executor object
- command-runner wrapper
- callable collaborator

## Structured result contract
The workflow result must use deterministic primitive fields only.

Required fields:
- `task_name: str`
- `status: str`
- `outcome: str`
- `next_action: str`
- `requires_approval: bool`

Optional fields:
- `reason: str`
- `review_mergeable: bool`

Do **not** return raw mock objects.

## No-task contract
If no pending task exists, return a deterministic no-op result:
- `task_name = "none"`
- `status = "no_task"`
- `outcome = "noop"`

## Success-path contract
If task execution succeeds and review/policy allow progress:
- `status = "completed"`
- `outcome = "ready_for_pr"` or similarly explicit deterministic value

## Failure-path contract
If task execution fails:
- use the classifier output
- use repair decision output
- return deterministic fields reflecting the chosen next action

## Test guidance
Tests must cover at least:
- no pending task
- execution success + review success
- execution success + review blocked
- execution failure + classified repair action
- approval-required result

Tests must use injected fakes/mocks for execution/review/policy/repair decisions.
Do not depend on live git/GitHub calls.

## Portability requirement
Do not hardcode TradingBot-specific commands or task names in the workflow engine.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- tests cover the workflow branches above
- implementation uses injected collaborators rather than hardcoded shell behavior
- output is deterministic and primitive-valued
