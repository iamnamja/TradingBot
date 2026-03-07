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

## Backward-compatibility requirements
This task extends the orchestrator runner built in earlier tasks.

It must preserve the already-established runner contracts unless this task explicitly adds fields.

This is the most important rule in the task.

### Existing no-task contract
If no pending task exists in normal mode, `run_next_task()` must continue to return at least:
- `task_name = "none"`
- `status = "no_task"`
- `message = "No pending tasks available."`

### Existing dry-run no-task contract
If no pending task exists in dry-run mode, `run_next_task(dry_run=True)` must continue to return at least:
- `task_name = "none"`
- `status = "no_task"`
- `dry_run = True`

### Existing normal pending-task contract
If a pending task exists in normal mode, existing tests may still expect:
- `task_name` to be the selected task name
- `status = "running"` for the immediate runner result

Do **not** silently change that established immediate result to `"completed"` unless the task explicitly stages a second result object.

## Required workflow
The workflow should do all of the following in order:

1. determine the next pending task
2. represent the task as running
3. invoke the task execution step through an injected collaborator or command wrapper
4. inspect the execution result
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

## Audit-path contract
This is the second most important rule in the task.

The runner must **not** assume that `ProjectConfig` already contains an `audit_path` field.

Acceptable approaches:
- make audit logging optional when no audit path is configured
- inject an audit writer/callback instead of a file path
- derive a safe explicit file path only when configuration provides one
- allow tests to stub/override audit behavior

Do **not** write to `tasks/` as if it were a file.
Do **not** assume any directory path is a valid appendable log file.

Tests must not fail because the runner attempts to open a directory path for audit logging.

## Structured result contract
Workflow results must use deterministic primitive fields only.

Required fields in the workflow result:
- `task_name: str`
- `status: str`
- `outcome: str`
- `next_action: str`
- `requires_approval: bool`

Additional fields may be added, but existing fields from prior tasks must remain compatible.

Do **not** return raw mock objects.

## Compatibility guidance for status values
Because earlier runner tests already exist, prefer this interpretation:

### Immediate runner status
The immediate return from `run_next_task()` in normal mode may still use:
- `status = "running"`

### Workflow outcome
Use a separate field for the higher-level decision, such as:
- `outcome = "ready_for_pr"`
- `outcome = "review_blocked"`
- `outcome = "repair_required"`
- `outcome = "approval_required"`
- `outcome = "noop"`

This avoids breaking earlier tests that assert `status == "running"`.

## No-task contract
If no pending task exists, return a deterministic no-op result that includes:
- `task_name = "none"`
- `status = "no_task"`
- `outcome = "noop"`
- `next_action = "none"`
- `requires_approval = False`
- `message = "No pending tasks available."`

In dry-run no-task mode, include:
- `dry_run = True`

## Success-path contract
If task execution succeeds and review/policy allow progress:
- keep immediate runner `status = "running"` if needed for compatibility
- use `outcome = "ready_for_pr"` or similarly explicit deterministic value
- set `next_action` deterministically

## Failure-path contract
If task execution fails:
- use the classifier output
- use repair decision output
- return deterministic fields reflecting the chosen next action

## Test guidance
Tests must cover at least:
- no pending task
- no pending task in dry-run
- execution success + review success
- execution success + review blocked
- execution failure + classified repair action
- approval-required result

Tests must use injected fakes/mocks for execution/review/policy/repair decisions.
Do not depend on live git/GitHub calls.
Do not require a real audit file path unless the test explicitly provides one.

## Portability requirement
Do not hardcode TradingBot-specific commands or task names in the workflow engine.

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- tests cover the workflow branches above
- implementation uses injected collaborators rather than hardcoded shell behavior
- output is deterministic and primitive-valued
- implementation preserves the previously established runner contracts listed above
- implementation does not assume `ProjectConfig.audit_path` exists
