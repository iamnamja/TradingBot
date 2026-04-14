# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 180.

The repo can now honestly claim a materially hardened one-task lane with:

- proof-task admission gating on exact deliverable contracts
- strict no-manual-intervention benchmark scoring
- deliverable-contract and completion-integrity enforcement
- authority corroboration and conservative run truth
- empty-bundle retry shaping and durable transport diagnostics
- runtime-artifact hygiene and subset-preservation normalization
- a threshold-based promotion artifact for the one-task lane
- a defined default-path posture for eligible one-task work and an explicit two-task pilot gate
- a bounded supervised two-task canary benchmark flow and re-proof checkpoint integrated alongside the one-task artifacts
- a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus with a durable corpus benchmark and promotion/checkpoint artifact

Use `tasks/README.md` as the canonical task-order index, `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative, and `docs/ORCHESTRATOR_BOUNDED_TWO_TASK_PILOT_OPERATIONS.md` as the operator-facing guide for the 176–180 tranche.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- a bounded supervised two-task pilot lane is ready and explicitly measured by canary and corpus-backed artifacts
- widening beyond one-task still requires explicit proof, not aspiration

It does not claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Two-task pilot re-proof verdict and product checkpoint

- Bounded two-task pilot verdict (canary + corpus): ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus, under supervision, using the explicit admission, handoff, role-split, and pilot truth persisted in `canary_*` artifacts and the bounded-corpus `bounded_corpus_promotion.json`.
- Widening checkpoint: cautious widening of the curated pair corpus may be considered only under supervision and only when corpus metrics remain within conservative thresholds. Broad unattended multi-task autonomy remains blocked. Standalone orchestrator-as-its-own-app remains blocked.
- Product-direction checkpoint: the orchestrator continues to operate inside this monorepo with a stable boundary and consumer bridge until broader multi-task autonomy proof is achieved.

## Next continuation target

Stay conservative while operating the bounded supervised pilot:

- continue running the exact two-task pilot runner with a pair-level session ledger
- keep the curated adjacent-pair corpus and admission manifest as the source of truth for pilot scope
- persist supervised-intervention truth explicitly so human help never gets misclassified as autonomous success
- benchmark the real bounded pilot runner against the curated pair corpus and record `bounded_corpus_promotion.json`
- only consider widening after real pilot corpus artifacts justify the next step, and keep one-task truth surfaces unchanged
