# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 156**.

The orchestrator now has:

- a bounded external-safe one-task execution lane,
- bounded multi-agent dev / test / repair / controller artifacts,
- external-safe failure taxonomy and targeted self-heal routing,
- pass-rate scoreboarding and failure digesting,
- a truthful two-task readiness gate,
- a bounded lint-only preflight normalization step,
- and a first benchmark harness proving mode for one-task work.

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative current status narrative.

## What the repo can honestly claim today

It can honestly claim:

- one external-safe allowlisted task at a time can run through a bounded supervised autonomous lane,
- the system can classify ordinary one-task failures and attempt bounded self-heal,
- benchmark-style one-task proving is now the main continuation mode,
- the repo still preserves a truthful no-go gate against widening to two-task work prematurely.

It does **not** honestly claim:

- broad unattended scheduler autonomy,
- reliable multi-task autonomous execution,
- self-hosting control-plane autonomy,
- that the orchestrator is already the default trusted execution path for all future tasks.

## Next continuation target

Shift from broad proof-mode planning into a **single-task reliability sprint**:

- integrate strict scorecarding into the benchmark/session surfaces,
- harden empty-bundle transport handling,
- normalize runtime artifact quarantine and subset-preservation leftovers,
- add a completion-integrity gate so helper-only partials do not look complete,
- then run a small one-task re-proof pack before resuming the broader roadmap.
