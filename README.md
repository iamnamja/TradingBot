# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 158**.

The bounded supervised slice plus narrow safe autonomous one-task lane now covers:

- proof-task admission gating on exact deliverable contracts
- bundle failure classification and targeted retry shaping
- hosted-authority operational convergence truth around the stable `ci-required` contract
- safe task-family autonomy allowlisting for ordinary one-task work
- a dedicated autonomous single-task runner with ledger, canary metrics, recovery reporting, supervised handoff, bounded resume state, and operator proof bundle
- scheduler routing through that bounded runner when exactly one safe task is ready
- conservative stop / requeue / supervised handoff for mixed queues

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative bounded-scope status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice plus a narrow one-task autonomous canary lane.

It can honestly claim:

- one allowlisted safe task at a time can run under supervision
- out-of-lane work is explicitly handed back to supervision instead of widened into broader autonomy
- operators have a small proof bundle showing what the lane can do and what it still refuses to do

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- arbitrary multi-task autonomous execution
- arbitrary self-hosting control-plane autonomy

## Next continuation target

Shift from “more safe-lane plumbing” to **execution quality**:

- define a canonical external-safe one-task evaluation corpus
- make the bounded one-task lane behave like a real dev / test / repair / controller loop
- improve targeted self-heal quality on ordinary external-safe failures
- measure pass rate and dominant failure classes
- only then decide whether bounded two-task trials are justified
