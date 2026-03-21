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
5. machine-readable contract directives
6. validator plugins

The runner applies the bundle, runs validators, and retries up to 4 times, but green checks alone are not sufficient if the bundle violates task policy.

## Product goals

- automate the current human-in-the-loop task workflow
- preserve safety and branch discipline
- reduce manual triage of failures
- support repeatable delivery across different software projects
- provide clear auditability for every decision
- minimize task-spec patching by making the harness more semantically aware
- separate spec clarification from execution when tasks are ambiguous

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
- machine-readable task contract enforcement
- protected API semantic preflight
- runtime artifact quarantine
- spec-mode and execution-mode workflow
- validator plugin support
- project bootstrap support
- safe parallel task execution for explicitly independent work

## Current implementation status

| Capability | Status | Task |
|-----------|--------|------|
| Backlog/state tracking | ✅ | 015–020 |
| Review/compliance checking | ✅ | 016 / 033 |
| Failure classification | ✅ | 017 |
| PR/CI/merge management | ✅ | 018 / 035 |
| Repair workflow | ✅ | 019 |
| Project adapter foundation | ✅ | 020 |
| Real task execution bridge | ✅ | 031 |
| Persistent backlog state | ✅ | 037 |
| Run loop / CLI / decision logging | ✅ | 038a–038c |
| Repo-local import symbol validation | ✅ | 038d |
| Harness semantic hardening tranche | ✅ | 039a–039c |
| End-to-end integration harness | ✅ | 040 |
| Multi-project hardening | ✅ | 041a–041b |
| Harness modularization | 🔜 | 042 |
| Runtime artifact quarantine | 🔜 | 043 |
| Spec / execution two-phase workflow | 🔜 | 044 |
| Structured failure journal | 🔜 | 045 |
| Project bootstrap adapter | 🔜 | 046 |
| Verification plugins / validators | 🔜 | 047 |
| Safe parallelism | 🔜 | 048 |

## Safety model

### Always automatic

- clean-worktree check
- task branch creation
- local validator execution
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

## High-level architecture target

```
src/builder/orchestrator/
    runner.py
    backlog.py
    state.py
    execution_result.py
    review.py
    policy.py
    git_guardrails.py
    merge.py
    command_runner.py
    approval.py
    audit.py
    failures.py
    repair.py
    project_config.py
    project_adapter.py
    cli.py

agents/
    run_task.py                — thin task shell
    lib/
        bundle_parser.py
        task_contracts.py
        protected_file_policy.py
        semantic_preflight.py
        check_runner.py
        git_ops.py
        provider_client.py
        artifact_quarantine.py
        spec_mode.py
        failure_journal.py
        validator_runner.py
```

## Success criteria

The orchestrator is production-usable when it can:

- run a task loop end to end
- stop safely on risky situations
- resume after interruption
- explain every action taken
- support at least two project adapters cleanly
- bootstrap a new project with minimal manual setup
- reject green-but-policy-violating bundles
- reject obviously invalid protected API usage before burning full test iterations
- quarantine known runtime artifacts automatically without weakening policy
- switch cleanly between spec generation and execution
