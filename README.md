# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized proof checkpoint is now complete through **Task 153**.

The bounded supervised slice plus narrow safe autonomous one-task lane now covers:

- proof-task admission gating on exact deliverable contracts
- bundle failure classification and targeted retry shaping
- hosted-authority operational convergence truth around the stable `ci-required` contract
- safe task-family autonomy allowlisting for ordinary one-task work
- a dedicated autonomous single-task runner with ledger, canary metrics, recovery reporting, supervised handoff, bounded resume state, and operator proof bundle
- scheduler routing through that bounded runner when exactly one safe task is ready
- conservative stop / requeue / supervised handoff for mixed queues
- a canonical external-safe evaluation corpus and evaluation manifest
- a deterministic developer / verifier / repair / controller record for each admitted one-task run
- an external-safe failure taxonomy and bounded self-heal router
- a pass-rate scoreboard, failure digest, and fresh external-safe re-proof showing a current supervised pass-rate band of roughly two-thirds on the corpus

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` for the authoritative bounded-scope status narrative.

## What the repo can honestly claim today

Today the repo has deterministic local proof for a bounded supervised multi-project slice plus a narrow one-task autonomous lane that has now been re-proved on the external-safe corpus.

It can honestly claim:

- one allowlisted safe task at a time can run under supervision
- out-of-lane work is explicitly handed back to supervision instead of widened into broader autonomy
- operators have proof artifacts showing what the lane can do, the current roughly two-thirds supervised pass-rate band on the external-safe corpus, and what it still refuses to do

It does **not** claim:

- broad unattended scheduler autonomy
- arbitrary protected/controller/meta task-family autonomy
- arbitrary multi-task autonomous execution
- arbitrary self-hosting control-plane autonomy

## Current measured execution-quality band

The current external-safe re-proof supports a truthful supervised one-task pass-rate band of roughly **4 completed runs out of 6 corpus items**. Two of those completions came after bounded self-heal, while the remaining non-completions stayed bounded as a lint-only failure and a hosted-authority/no-checks block.

## Next continuation target

Use that evidence to decide whether bounded two-task trials are justified without widening the claim early.
