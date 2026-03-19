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

## What has been built

### Core infrastructure (tasks 001–010)

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

### Paper-trading readiness layer (tasks 011–014)

- Alpaca broker adapter
- portfolio/account state loader
- position sizing and intent planner
- manual paper-trading cycle command

## Current milestone

**Manual paper-trading readiness.**

The repository contains the pieces needed to run a one-shot paper-trading cycle manually once credentials and environment configuration are in place.

## Task status summary

| Range | Status | Notes |
|-------|--------|------|
| 001–003 | ✅ Complete | Done manually |
| 004–014 | ✅ Complete | Done via agent workflow |
| 031 | ✅ Complete | Orchestrator real execution bridge |
| 037 | ✅ Complete | Persistent backlog state completed manually and merged |
| 032–036, 038–040 | 🔄 In progress | Orchestrator hardening |

## What still remains for TradingBot

These are functional milestones after orchestrator work completes:

- scheduled recurring execution during market hours
- symbol universe management
- duplicate-order / idempotency guard
- execution reconciliation / order status follow-up
- reporting / summaries / dashboards
- backtesting and simulation
- stronger portfolio/risk controls
- live-mode safety gates and approvals

## Paper-trading readiness definition

The project is paper-trading ready when:

- manual paper-cycle command succeeds with real paper credentials
- paper orders can be submitted safely
- audit logs are produced cleanly
- account/position state is loaded correctly
- generated order intents are explainable and deterministic
- runtime artifacts do not dirty the repo
- safety guard prevents live mode unless explicitly approved

## Controls already in place

- task-per-branch discipline
- CI-gated merge (PR required, no direct pushes to main)
- clean-worktree enforcement in runner
- task deliverable enforcement
- repo-aware import validation
- retry + semantic failure handling
- Windows-compatible subprocess handling

## Key lessons learned from agent workflow

| Lesson | Impact |
|--------|--------|
| Vague task specs cause agent drift | Specs must include exact contracts, forbidden patterns, and pseudocode for algorithmic methods |
| `simulate_backlog` loop pattern is fragile | Must use `get_next_task([])` directly; `continue` not `break` on approval |
| `ProjectConfig` must stay mutable | Never use `@dataclass(frozen=True)` |
| Empty `changed_files` must return `mergeable: True` | Never block review solely on empty file list |
| Failure message format matters exactly | `"Execution failed: {text}"` not `"Execution failed."` |
| Protected files need narrow scopes | `runner.py` changes should be additive-only or isolated into their own task |
| Green tests are not sufficient | The harness must also enforce task-policy compliance |
| Windows compatibility matters | Never use `echo` as subprocess command; always use `sys.executable` |

## Why orchestrator work comes next

The current workflow still requires manual coordination:

- selecting the next task
- running the task
- interpreting failures
- deciding whether to patch code, task specs, runner, or CI
- creating/merging PRs
- continuing to the next task

The orchestrator automates that delivery loop safely. Once the remaining orchestrator hardening tasks are complete, the focus returns to TradingBot product functionality.
