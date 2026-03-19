# Orchestrator Product Specification

## Purpose

The orchestrator is a reusable software-delivery engine that takes a backlog of task specifications, executes them safely through coding agents, reviews the results, classifies failures, manages pull requests and CI, and continues iteratively with strong controls.

TradingBot is the first client project. The orchestrator must support future software projects with minimal changes.

## Agent and harness model

The coding model/provider is configurable. The reliable control surface is:

1. the task spec
2. the harness
3. protected-file policies
4. review/compliance checks

The runner applies the bundle, runs `ruff` + `pytest`, and retries up to 4 times, but green tests alone are not sufficient if the bundle violates task policy.

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
- execution result normalization
- result review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow handling
- project adapter/config abstraction
- looped orchestration across tasks
- decision journaling
- resumable execution after approval checkpoints
- dry-run simulation
- protected-file policy enforcement

## Current implementation status

| Capability | Status | Task |
|-----------|--------|------|
| Backlog/state tracking | ✅ | 015–020 |
| Review/compliance checking | ✅ | 016 |
| Failure classification | ✅ | 017 |
| PR/CI/merge management | ✅ | 018 |
| Repair workflow | ✅ | 019 |
| Project adapter foundation | ✅ | 020 |
| Real task execution bridge | ✅ | 031 |
| Persistent backlog state | ✅ | 037 |
| Execution result normalization | 🔄 | 032 |
| Real review + compliance gate | 🔄 | 033 |
| Branch/worktree guardrails | 🔄 | 034 |
| PR creation workflow | 🔄 | 035 |
| Resume after approval | 🔄 | 036 |
| Run loop engine | 🔄 | 038 |
| CLI wiring + integration harness | 🔄 | 039 |
| Multi-project hardening | 🔄 | 040 |

## Safety model

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

```
src/builder/orchestrator/
    runner.py           — main orchestration loop
    backlog.py          — task discovery and state
    state.py            — OrchestratorState model
    execution_result.py — normalization layer
    review.py           — compliance checker
    policy.py           — policy engine
    git_guardrails.py   — branch/worktree safety
    merge.py            — PR creation
    command_runner.py   — safe subprocess abstraction
    approval.py         — checkpoint management
    audit.py            — decision logging
    failures.py         — failure classifier
    repair.py           — repair workflow
    project_config.py   — config schema
    project_adapter.py  — project adapters
    cli.py              — CLI entry point
```

## Invariants that must never change

### runner.py invariants

- `OrchestratorRunner.__init__(config, backlog_tracker, initial_state)` — signature never changes
- `run_next_task(dry_run=False)` — signature never changes
- `simulate_backlog()` — signature and return keys never change
- legacy success: `status="running"`, `message="Task is now running."`, `outcome="ready_for_pr"`
- empty `changed_files` → `run_review` returns `{"mergeable": True}`
- `simulate_backlog` calls `get_next_task([])` directly and uses `continue`, not `break`, on approval

### config invariants

- `ProjectConfig` is never `@dataclass(frozen=True)`
- optional config fields are always accessed via `getattr(self.config, "field", default)`
- `get_tradingbot_default_config()` and `get_generic_project_config()` remain on `ProjectAdapter`

## Success criteria

The orchestrator is production-usable when it can:

- run a task loop end to end
- stop safely on risky situations
- resume after interruption
- explain every action taken
- support at least one project adapter cleanly
- be extended to another project with minimal engine changes
- reject green-but-policy-violating bundles
