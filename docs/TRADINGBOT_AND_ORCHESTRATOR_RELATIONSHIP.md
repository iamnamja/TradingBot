# TradingBot and Orchestrator Relationship

## Two products in one repository

This repository contains two related but distinct products.

### 1. TradingBot

A safe, testable algorithmic trading bot with paper-trading readiness. This remains the immediate product goal.

### 2. Orchestrator

A reusable software-delivery engine that builds and evolves software projects through a task-driven agent workflow. TradingBot is its first client and testbed.

## Why this separation matters

The orchestrator must not be tightly coupled to TradingBot. TradingBot is the first project adapter — not the permanent center of the orchestration engine. The orchestrator must be portable enough to drive future software projects with minimal changes.

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
- real task execution bridge (task 031 ✅)
- persistent backlog state (task 037 ✅)

Pending hardening:

- execution result normalization
- real review and compliance gate
- branch/worktree guardrails
- PR creation workflow
- resume after approval
- run loop engine
- CLI wiring
- end-to-end integration harness
- multi-project hardening

## Agent model and control surface

The orchestrator can be run with different providers/models, but the primary control surface is the task spec plus the harness.

Key lesson:

- precise task specs with exact implementation guidance, forbidden patterns, and protected-file rules produce reliable results
- vague or overly broad specs produce drift, even if the model eventually gets tests green

## Relationship diagram

```
Orchestrator (engine)
    └── ProjectAdapter (TradingBot config)
            └── TradingBot tasks backlog
                    └── Coding agent
```

## Long-term intent

- Orchestrator drives TradingBot to completion
- Orchestrator is then reusable to bootstrap future software projects
- Same core engine, different project adapters and policies
