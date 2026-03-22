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
- support multiple software projects through adapters and config
- evolve from a project-specific harness into a reusable product

TradingBot remains the first client and testbed, but the orchestrator is now explicitly being productized for reuse across future projects.

## Core design principle

Separate the system into three layers.

### 1. Generic orchestration engine (`src/builder/orchestrator/`)

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
- project configuration and adapter support

### 2. Harness / agent shell (`agents/`)

Responsible for:

- task prompt construction
- file-bundle parsing
- protected-file handling
- static contract enforcement
- semantic preflight
- provider/model execution
- local check execution
- branch-oriented task loop integration

This layer is now materially modularized, but the shell still needs convergence before it is truly thin and package-ready.

### 3. Project adapter / project config

Project-specific behavior:

- tasks directory location
- lint/test commands
- branch naming rules
- protected files
- risky file patterns
- deliverable parser rules
- merge policies
- environment/bootstrap expectations
- task templates
- project-specific validators
- safe-parallelism defaults

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
- preserve raw failure evidence for retries rather than over-compressing it too early
- use direct patches when repeated retries keep corrupting the same protected surface

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
- packaging / extraction surface changes

### Safety controls

- never auto-enable live trading
- enforce paper-mode guards where relevant
- prevent autonomous merging of risky/meta changes without approval
- allow safe automation only when the change is structurally recoverable and policy-compliant

## Lessons from tasks 043–048

The orchestrator is now good enough that the next leverage comes from **stabilizing product boundaries**, not from adding more engine features.

Key lessons:

- task quality is as important as model quality
- direct curated patches can be safer than repeated reruns for shell-sensitive work
- `run_task.py` is functionally strong but structurally still too monolithic
- runtime artifacts can now be auto-quarantined safely
- ambiguity can be handled in a spec-generation phase before execution
- validator selection belongs in config/adapters, but legacy wrapper behavior still matters
- safe parallelism must be layered onto the real runner surface, not replace it
- project reusability now depends on interface freeze and portability proof more than on adding new features

## Portability requirements

To make the orchestrator reusable across future software builds:

- do not hardcode TradingBot-specific paths in the engine
- store project behavior in config/adapters
- make task parsing configurable
- make lint/test commands configurable
- allow project-specific protected-file patterns
- keep merge criteria configurable
- use `getattr` for optional config fields where appropriate
- support project-specific validator plugins
- support bootstrapping a new project adapter without engine edits
- prove a second project fixture before extraction

## What success looks like now

The orchestrator is successful when it can:

- take a backlog of tasks
- autonomously complete routine tasks
- open and merge safe PRs
- stop intelligently when human approval is needed
- leave a clear audit trail of what happened and why
- reject green-but-policy-violating bundles
- run the same engine against a second project with only a config change
- bootstrap a third project with a scaffold command rather than manual repo surgery
- expose a frozen public surface that can later move to its own package/repo
