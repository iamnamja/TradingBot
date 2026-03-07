# TradingBot Project State

## Objective
Build a safe, testable algorithmic trading bot that can:
- fetch market data
- compute indicators
- generate deterministic candidates
- optionally apply LLM review
- enforce risk checks
- create order intents
- execute through a broker adapter
- run an end-to-end cycle with audit logging
- support paper trading before any live trading

## What has been built so far
### Core infrastructure
- project structure and config baseline
- market-hours guard
- data layer
- indicators
- deterministic strategy
- LLM advisor abstraction
- risk gate
- execution engine
- cycle runner
- audit logging

### Paper-trading readiness layer
- Alpaca broker adapter
- portfolio/account state loader
- position sizing and intent planner
- manual paper-trading cycle command

## Current milestone
The project is now at:
- **manual paper-trading readiness**

This means the repository contains the pieces needed to run a one-shot paper-trading cycle manually once credentials and environment configuration are in place.

## Current status by task
- 001–003: completed manually
- 004–014: completed through the task-driven agent workflow, hardened through iterative task and runner improvements

## Current strengths
- end-to-end task-driven development workflow
- branch-per-task discipline
- CI-gated merge workflow
- increasingly hardened task specs
- reusable agent runner with deliverable enforcement, repo awareness, import validation, and retry logic
- testable abstractions across major bot layers

## What still remains for the TradingBot itself
These are likely next functional milestones after the orchestrator work:
- scheduled recurring execution during market hours
- symbol universe management
- duplicate-order / idempotency guard
- execution reconciliation / order status follow-up
- reporting / summaries / dashboards
- backtesting and simulation
- stronger portfolio/risk controls
- live-mode safety gates and approvals

## Paper-trading readiness definition
The project should be considered paper-trading ready when:
- manual paper-cycle command succeeds with real paper credentials
- paper orders can be submitted safely
- audit logs are produced cleanly
- account/position state is loaded correctly
- generated order intents are explainable and deterministic
- runtime artifacts do not dirty the repo
- safety guard prevents live mode unless explicitly approved

## Current controls already in place
- do not work directly on main
- task-per-branch
- CI-gated merge process
- clean-worktree enforcement in runner
- task deliverable enforcement
- repo-aware import validation
- retry + semantic failure handling
- log artifact hygiene improvements

## Risks / lessons learned so far
- ambiguous task specs lead to agent drift
- algorithmic tasks need normative examples or pseudocode
- CI dependency mismatches can break seemingly correct code
- runtime artifacts must be isolated from repo state
- patch target guidance is critical in tests
- task parser sensitivity to backticked paths must be respected

## Why the next step is the orchestrator
The current workflow still requires manual coordination:
- selecting the next task
- running the task
- interpreting failures
- deciding whether to patch code, task specs, runner, or CI
- creating/merging PRs
- continuing to the next task

The orchestrator layer is intended to automate that delivery loop safely.
