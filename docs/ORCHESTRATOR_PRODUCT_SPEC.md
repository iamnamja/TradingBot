# Orchestrator Product Specification

## Purpose
The orchestrator is a reusable software-delivery engine that can take a backlog of task specifications, execute them safely through coding agents, review the results, classify failures, manage pull requests and CI, and continue iteratively with strong controls.

The TradingBot repository is the first client project for this orchestrator, but the orchestrator must be designed to support future software projects as well.

## Product goals
- automate the current human-in-the-loop task workflow
- preserve safety and branch discipline
- reduce manual triage of failures
- support repeatable delivery across different software projects
- provide clear auditability for every decision

## Non-goals
- no direct work on `main`
- no autonomous live-trading enablement
- no silent weakening of tests, CI, or approval controls
- no project-specific hardcoding in the core engine

## Core capabilities
- backlog/task discovery
- state tracking
- result review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow handling
- project adapter/config abstraction
- looped orchestration across tasks
- decision journaling
- resumable execution
- dry-run simulation

## Safety model
The orchestrator should be able to act automatically only inside defined safety boundaries.

### Always automatic
- clean-worktree check
- task branch creation
- local lint/test execution
- deliverable review
- runtime artifact detection
- task state update

### Automatic if policy allows
- PR creation
- auto-merge after passing CI
- safe retries
- cleanup of known runtime artifacts
- ordinary task-spec patch workflow

### Approval required
- CI/workflow changes
- runner changes
- dependency changes
- secrets/auth handling
- live-trading related changes
- changes to protected/meta files
- repeated failure beyond retry policy
- broad adapter/policy changes

## High-level architecture
### Core engine
Generic, reusable modules under:
- `src/builder/orchestrator/`

### Project layer
Project-specific behavior through:
- project config schema
- project adapters
- policy config

### Audit layer
Decision logs, action logs, and resumable state.

## Success criteria
The orchestrator is considered production-usable when it can:
- run a task loop end to end
- stop safely on risky situations
- resume after interruption
- explain every action taken
- support at least one project adapter cleanly
- be extended to another project with minimal engine changes
