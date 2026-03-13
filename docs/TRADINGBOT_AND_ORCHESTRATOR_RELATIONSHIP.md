# TradingBot and Orchestrator Relationship

## Two products in one repository

This repository contains two related but distinct products:

### 1. TradingBot
A safe, testable algorithmic trading bot with paper-trading readiness. The immediate product goal.

### 2. Orchestrator
A reusable software-delivery engine that builds and evolves software projects through a task-driven agent workflow. TradingBot is its first client and testbed.

## Why this separation matters

The orchestrator must not be tightly coupled to TradingBot. TradingBot is the first project adapter — not the permanent center of the orchestration engine. The orchestrator must be portable enough to drive future software projects with minimal changes.

## Current TradingBot status (as of task 031)

- Tasks 001–003: completed manually
- Tasks 004–014: completed through the task-driven agent workflow
- Current milestone: **manual paper-trading readiness**
- The bot can run a one-shot paper-trading cycle once credentials and environment are in place

## Current orchestrator status (as of task 031)

Completed and stable:
- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation
- real task execution bridge (task 031 ✅)

In progress (tasks 032–040):
- execution result normalization
- real review and compliance gate
- branch/worktree guardrails
- PR creation workflow
- resume after approval
- persistent backlog state
- run loop CLI
- end-to-end integration harness
- multi-project hardening

## Agent model

The orchestrator runs a **Claude Sonnet** agent (via Anthropic API) to implement each task. The agent:
- reads a task markdown spec
- produces a file bundle (BEGIN_FILE_BUNDLE / END_FILE_BUNDLE format)
- the runner applies the bundle, runs ruff + pytest, and retries up to 4 times

Key lesson: the task spec is the primary control surface. Precise specs with exact implementation guidance, forbidden patterns, and explicit contracts produce green results in 1 iteration. Vague specs produce multi-iteration failures.

## Relationship diagram

```
Orchestrator (engine)
    └── ProjectAdapter (TradingBot config)
            └── TradingBot tasks backlog
                    └── Dev agent (Claude Sonnet)
```

## Long-term intent

- Orchestrator drives TradingBot to completion
- Orchestrator is then reusable to bootstrap future software projects
- Same core engine, different project adapters and policies
