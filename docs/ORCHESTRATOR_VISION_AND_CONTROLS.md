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

This orchestrator should work for TradingBot first, but be portable enough to reuse on future software projects.

## Core design principle
Separate the system into:

### Generic orchestration engine
Reusable across projects:
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
Project-specific:
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
Responsible for:
- selecting the next task
- tracking task state
- invoking the dev agent
- invoking review/compliance logic
- deciding next actions
- writing orchestration decisions to an audit trail

### 2. Dev agent
Responsible for:
- implementing one task
- producing the required files
- running local checks via the current task runner
- pushing the task branch

### 3. Review / QA agent
Responsible for:
- verifying deliverables
- checking scope compliance
- detecting runtime artifacts
- evaluating whether a PR is mergeable
- identifying suspicious or out-of-scope changes

### 4. Failure-classifier / repair agent
Responsible for:
- determining whether a failure is caused by:
  - implementation bug
  - task ambiguity
  - runner weakness
  - CI/dependency issue
  - repo hygiene issue
- recommending the right remediation path

### 5. Merge manager
Responsible for:
- PR creation
- CI polling
- merge policy enforcement
- syncing main after merge

## Controls
These controls should be mandatory.

### Repo controls
- require a clean worktree before starting
- never commit directly to main
- always create one task branch per task
- sync main before each new task

### Retry controls
- cap automatic retries
- do not loop forever
- if the same failure repeats, escalate instead of blindly retrying

### Scope controls
- reject or flag changes that touch unrelated files
- detect committed runtime artifacts
- detect unapproved workflow/meta changes

### Approval gates
Human approval should be required for:
- task-runner changes
- CI/workflow changes
- dependency management changes
- task spec rewrites
- secrets or credentials handling
- live-trading related behavior
- destructive or cross-cutting repository changes

### Safety controls
- never auto-enable live trading
- enforce paper-mode guards where relevant
- prevent autonomous merging of risky/meta changes without approval

## Portability requirements
To make the orchestrator reusable across future software builds:
- do not hardcode TradingBot-specific paths in the engine
- store project behavior in config/adapters
- make task parsing configurable
- make lint/test commands configurable
- allow project-specific “protected file” patterns
- keep merge criteria configurable

## What success looks like
The orchestrator is successful when it can:
- take a backlog of tasks
- autonomously complete routine tasks
- open and merge safe PRs
- stop intelligently when human approval is needed
- leave a clear audit trail of what happened and why
