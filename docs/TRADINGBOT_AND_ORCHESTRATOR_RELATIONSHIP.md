# TradingBot and Orchestrator Relationship

## Current repository reality

This repository contains **two products**:

1. **TradingBot** — the application being built
2. **Orchestrator** — the reusable software-delivery engine that is building and hardening the repository

TradingBot remains the first client project and the testbed for the orchestrator.

## Current TradingBot status

TradingBot is at **manual paper-trading readiness**.

That means the repository can support a controlled manual paper-trading cycle once credentials and environment are in place.

## Current orchestrator status

Completed and stable in substance:

- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation
- real task execution bridge
- persistent backlog state
- run-loop / CLI / decision-log surface
- repo-local import symbol validation
- harness semantic hardening
- deterministic end-to-end integration harness
- multi-project config/adapter hardening
- harness modularization tranche
- runtime artifact quarantine
- spec/execution split
- structured failure journaling
- bootstrap/project adapter scaffolding
- validator plugins
- safe parallelism controls

## Where the relationship stands now

The orchestrator is already a second product, but it is **not yet ready to be split cleanly**.

Why:
- the core feature set through 048 is now present
- but the public surface is not frozen yet
- `agents/run_task.py` is still too monolithic
- portability has not yet been proven with a second non-TradingBot project fixture
- the docs still lag the real baseline

## Recommendation on repo separation

### Recommendation: **separate later, after one more stabilization tranche**

A split now is possible, but still premature.

Best path:
1. finish the 049–054 stabilization tranche
2. freeze the public orchestrator surface
3. prove second-project portability
4. then extract/package the orchestrator
5. leave TradingBot as the first client adapter

## Best eventual split model

When the split happens, use this structure:

### Orchestrator repository

Contains:
- `src/builder/orchestrator/...`
- `agents/...`
- shared docs and task templates
- bootstrap tooling
- generic validator/plugin framework
- public config / adapter / task-spec documentation

### TradingBot repository

Contains:
- `src/tradingbot/...`
- `tests/...`
- TradingBot task backlog
- TradingBot project adapter/config
- orchestrator dependency pinned by version or git SHA

## Best migration approach

When ready to split:

1. freeze the public orchestrator surface
   - config schema
   - adapter interface
   - task spec format
   - validator interface
   - harness module layout

2. extract orchestrator history cleanly
   - use `git filter-repo` or `git subtree split`
   - preserve commit history for `src/builder/orchestrator` and `agents`

3. publish or pin the orchestrator
   - internal package, editable install, or git dependency

4. keep TradingBot as a client
   - maintain a TradingBot adapter package/config
   - keep project-specific tasks in the TradingBot repo

## Long-term intent

- Orchestrator continues to drive TradingBot to completion
- Orchestrator becomes reusable to bootstrap future software projects
- Same core engine, different project adapters and validator stacks
