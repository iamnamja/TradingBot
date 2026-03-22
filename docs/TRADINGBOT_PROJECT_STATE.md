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
| 042–048 | ✅ Complete | Orchestrator productization tranche complete in substance |
| 049–054 | 🔜 Next | Orchestrator stabilization / portability proof tranche |

## What still remains for TradingBot

These are functional milestones after the current orchestrator stabilization tranche:

- scheduled recurring execution during market hours
- symbol universe management
- duplicate-order / idempotency guard
- execution reconciliation / order status follow-up
- reporting / summaries / dashboards
- backtesting and simulation
- stronger portfolio/risk controls
- live-mode safety gates and approvals

## Why orchestrator work still comes next

The delivery loop is much stronger now, but the harness is still too monolithic for clean reuse across future projects.

The next orchestrator tranche is aimed at:

- converging `run_task.py` into a truly thin shell
- freezing the config / adapter / validator / task-spec public surface
- normalizing stale roadmap/product docs after 042–048
- proving the engine against a second project fixture
- adding integrated end-to-end scenarios for the new 043–048 capabilities
- preparing eventual package / repo extraction

That investment should reduce future task-spec patching and make the orchestrator reusable outside TradingBot without depending on TradingBot-specific assumptions.

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
- runtime artifact quarantine
- spec/execution mode split
- structured failure journaling
- bootstrap/project adapter scaffolding
- validator plugin support
- safe parallelism safeguards
- end-to-end integration coverage
- multi-project config/adapters

## Key lessons learned from agent workflow

| Lesson | Impact |
|--------|--------|
| Vague task specs cause agent drift | Specs must include exact contracts, forbidden patterns, and pseudocode where needed |
| Production baseline first, tests-only second works best | Large hardening tasks should be split into production tasks followed by validation tasks |
| `run_task.py` is powerful but still too large | The next tranche should converge and dedupe the shell before extraction |
| Runtime artifacts are repetitive but recoverable | Auto-quarantine should replace manual cleanup for known safe artifacts |
| Green tests are not sufficient | The harness must also enforce task-policy compliance |
| Windows compatibility matters | Always use cross-platform subprocess patterns |
| Direct patching sometimes beats repeated task reruns | For shell-sensitive work, a curated patch path can be safer than repeated blind retries |
| Project portability is real now | The next step is proof and interface freeze, not more TradingBot-specific logic |

## Long-term direction

TradingBot remains the first client project.

The orchestrator has now moved from “internal build tool for TradingBot” toward “reusable delivery product that can continue to build TradingBot and future apps.”
