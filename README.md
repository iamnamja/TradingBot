# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability checkpoint is now complete through **Task 165**.

The bounded supervised slice plus the narrow safe autonomous one-task lane now covers:

- proof-task admission gating on exact deliverable contracts
- bundle failure classification and targeted retry shaping
- hosted-authority operational convergence truth around the stable `ci-required` contract
- safe task-family autonomy allowlisting for ordinary one-task work
- a dedicated autonomous single-task runner with ledger, scorecard, canary metrics, recovery reporting, supervised handoff, bounded resume state, and operator proof bundles
- scheduler routing through that bounded runner when exactly one safe task is ready
- conservative stop / requeue / supervised handoff for mixed queues
- completion integrity gating for tasks that require live-surface integration
- runtime artifact hygiene normalization
- two sequential one-task reliability re-proofs

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative bounded-scope status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice plus a narrow one-task autonomous lane that has undergone repeated reliability re-proofs.

It can honestly claim:

- one allowlisted safe task at a time can run under supervision
- out-of-lane work is explicitly handed back to supervision instead of widened into broader autonomy
- operators have proof artifacts showing what the lane can do and what it still refuses to do
- the project is still in one-task reliability mode rather than broad autonomous expansion

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- arbitrary multi-task autonomous execution
- arbitrary self-hosting control-plane autonomy

## Next continuation target

Stay in **one-task reliability mode** for another slice:

- tighten strict no-manual scorecard truth
- improve authority corroboration and run-truth classification
- eliminate the dominant remaining one-task failure family
- run a formal promotion re-proof
- only then decide whether eligible one-task work should become the default orchestrator path and whether a bounded two-task pilot is justified
