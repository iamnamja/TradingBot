# Orchestrator Vision and Controls

## Vision

Build a reusable software-delivery orchestrator that can:

- manage a backlog of tasks
- run a coding agent against one task at a time
- validate results
- classify failures
- decide whether to retry, patch task specs, patch the runner, or stop for approval
- create and merge PRs when policy is satisfied
- continue automatically to the next task

This orchestrator works for TradingBot first, but is portable enough to reuse on future software projects.

## Core design principle

Separate the system into two layers.

### Generic orchestration engine

Reusable across projects (`src/builder/orchestrator/`):

- task queue handling
- branch lifecycle
- PR lifecycle
- CI status handling
- review/compliance checks
- retry policy
- failure classification
- approval gating
- decision audit logging

### Project adapter / project config

Project-specific behavior:

- tasks directory location
- lint/test commands
- branch naming rules
- protected files
- risky file patterns
- deliverable parser rules
- merge policies
- environment/bootstrap expectations

## Agent roles

### 1. Orchestrator

Selects the next task, tracks state, invokes the dev agent, invokes review/compliance logic, decides next actions, writes orchestration decisions to an audit trail.

### 2. Dev agent

Implements one task. Produces the required file bundle. Runs local checks via the task runner. Pushes the task branch.

### 3. Review / QA agent

Verifies deliverables, checks scope compliance, detects runtime artifacts, evaluates whether a PR is mergeable, and identifies suspicious or out-of-scope changes.

### 4. Failure-classifier / repair agent

Determines whether a failure is an implementation bug, task ambiguity, runner weakness, CI/dependency issue, or repo hygiene issue. Recommends the right remediation path.

### 5. Merge manager

Creates PRs, polls CI status, enforces merge policy, syncs `main` after merge.

## Controls

### Repo controls

- require a clean worktree before starting
- never commit directly to `main`
- always create one task branch per task
- sync `main` before each new task

### Retry controls

- cap automatic retries (max 4 iterations per task)
- do not loop forever
- if the same failure repeats, escalate instead of blindly retrying

### Scope controls

- reject or flag changes that touch unrelated files
- detect committed runtime artifacts
- detect unapproved workflow/meta changes
- treat task policy compliance as separate from test green-ness

### Approval gates

Human approval required for:

- task-runner changes
- CI/workflow changes
- dependency management changes
- task spec rewrites
- secrets or credentials handling
- live-trading related behavior
- destructive or cross-cutting repository changes
- protected-file policy exceptions

### Safety controls

- never auto-enable live trading
- enforce paper-mode guards where relevant
- prevent autonomous merging of risky/meta changes without approval

## Implementation invariants

These must be embedded in every orchestrator task spec going forward.

### simulate_backlog — only valid pattern

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
        continue
    planned_actions.append(f"Task {next_task.name} completed successfully.")
```

### run_review — empty files

- `changed_files=[]` → return `{"mergeable": True}` on legacy/mock path
- never block review solely because no files were changed

### ProjectConfig — always mutable

- never `@dataclass(frozen=True)`
- always `getattr(self.config, "field", default)` for optional fields

### Legacy success contract

- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

### Failure message contract

- `message == "Execution failed: {text}"` when failure_text or stderr is present
- read from `execution_result.get("failure_text") or execution_result.get("stderr") or ""`

### Windows compatibility

- never use `echo` as subprocess command in tests
- use `sys.executable + ["-c", "..."]` for cross-platform subprocess tests

## New lesson from tasks 037–038

The orchestrator needs stronger structural control, not just stronger prompts.

Green tests are necessary but not sufficient if the bundle violates the task's protected-file rules.

Future tasks should use one of these scopes explicitly:

- exact-copy-plus-append-method
- method-add-only
- tests-only
- config-only
- docs-only

## Portability requirements

To make the orchestrator reusable across future software builds:

- do not hardcode TradingBot-specific paths in the engine
- store project behavior in config/adapters
- make task parsing configurable
- make lint/test commands configurable
- allow project-specific protected-file patterns
- keep merge criteria configurable
- use `getattr` for all optional config fields

## What success looks like

The orchestrator is successful when it can:

- take a backlog of tasks
- autonomously complete routine tasks
- open and merge safe PRs
- stop intelligently when human approval is needed
- leave a clear audit trail of what happened and why
- reject green-but-policy-violating bundles
- run the same engine against a second project with only a config change
