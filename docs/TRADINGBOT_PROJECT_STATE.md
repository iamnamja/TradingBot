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
| 032–041 | ✅ Complete | Orchestrator hardening and portability tranche complete |
| 042–048 | 🔜 Planned | Orchestrator productization tranche |

## What still remains for TradingBot

These are functional milestones after the next orchestrator productization tranche:

- scheduled recurring execution during market hours
- symbol universe management
- duplicate-order / idempotency guard
- execution reconciliation / order status follow-up
- reporting / summaries / dashboards
- backtesting and simulation
- stronger portfolio/risk controls
- live-mode safety gates and approvals

## Why orchestrator work still comes next

The delivery loop is much stronger now, but the harness is still too monolithic for painless reuse across future projects.

The next orchestrator tranche is aimed at:

- modularizing `run_task.py`
- automatically quarantining known runtime artifacts
- separating spec clarification from execution
- recording structured failure history
- bootstrapping adapters for future projects
- supporting richer project-specific validators
- enabling safe limited parallelism

That investment is expected to reduce future task-spec patching and make the orchestrator reusable outside TradingBot.

## Controls already in place

- task-per-branch discipline
- CI-gated merge (PR required, no direct pushes to main)
- clean-worktree enforcement in runner
- task deliverable enforcement
- repo-aware import validation
- retry + semantic failure handling
- Windows-compatible subprocess handling
- machine-readable contract directives
- protected API semantic preflight
- end-to-end integration coverage
- multi-project config/adapters

## Key lessons learned from agent workflow

| Lesson | Impact |
|--------|--------|
| Vague task specs cause agent drift | Specs must include exact contracts, forbidden patterns, and pseudocode where needed |
| Production baseline first, tests-only second works best | Large hardening tasks should be split into production tasks followed by validation tasks |
| `run_task.py` is powerful but monolithic | The next tranche should modularize the harness before adding more behavior |
| Runtime artifacts are repetitive but recoverable | Auto-quarantine should replace manual cleanup for known safe artifacts |
| Green tests are not sufficient | The harness must also enforce task-policy compliance |
| Windows compatibility matters | Always use cross-platform subprocess patterns |
| Project portability is real now | The next step is bootstrap and validator extensibility, not just TradingBot-specific work |

## Long-term direction

TradingBot remains the first client project.

The orchestrator is now transitioning from “internal build tool for TradingBot” toward “reusable delivery product that can continue to build TradingBot and future apps.”
