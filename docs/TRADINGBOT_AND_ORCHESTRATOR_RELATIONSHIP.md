# TradingBot and Orchestrator Relationship

## Two products in one repository

This repository contains two related but distinct products.

### 1. TradingBot

A safe, testable algorithmic trading bot with paper-trading readiness. This remains the immediate application goal.

### 2. Orchestrator

A reusable software-delivery engine that builds and evolves software projects through a task-driven agent workflow. TradingBot is its first client and testbed.

## Why this separation matters

The orchestrator must not be tightly coupled to TradingBot. TradingBot is the first project adapter — not the permanent center of the orchestration engine.

The work through Task 041 has proven that the engine can already support multiple project configs. The next tranche is about turning that portability into a cleaner reusable product.

## Current TradingBot status

- Tasks 001–003: completed manually
- Tasks 004–014: completed through the task-driven agent workflow
- Current milestone: **manual paper-trading readiness**
- The bot can run a one-shot paper-trading cycle once credentials and environment are in place

## Current orchestrator status

Completed and stable:

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

Next productization tranche:

- modularize `run_task.py` into reusable modules
- auto-quarantine known runtime artifacts
- separate spec mode from execution mode
- persist a structured failure journal
- bootstrap new project adapters
- support validator plugins
- add safe limited parallelism

## Recommendation on repo separation

### Recommendation: **separate later, not immediately**

A split now is possible, but not yet optimal.

Why:
- the orchestrator is now clearly a second product
- the docs already treat it as a generic engine with project adapters
- but `run_task.py` and the surrounding harness are still being productized

Best path:
1. finish the 042–048 productization tranche
2. stabilize the module boundaries and bootstrap flow
3. then extract the orchestrator into its own repository/package
4. leave TradingBot as the first client adapter

## Best eventual split model

When the split happens, use this structure:

### Orchestrator repository

Contains:
- `src/builder/orchestrator/...`
- `agents/...`
- shared docs and task templates
- bootstrap tooling
- generic validator/plugin framework

### TradingBot repository

Contains:
- `src/tradingbot/...`
- `tests/...`
- TradingBot task backlog
- TradingBot project adapter/config
- orchestrator dependency pinned by version

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
