# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 175.

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

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- a bounded supervised two-task pilot lane has a conservative canary scorecard and re-proof checkpoint
- widening beyond one-task still requires explicit proof, not aspiration

It does not claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Two-task pilot re-proof verdict and product checkpoint

- Bounded two-task pilot verdict: ready for a bounded supervised two-task pilot, under supervision, using the explicit admission, handoff, and role-split truth persisted in canary artifacts and canary_promotion.json.
- Product-direction checkpoint: the standalone orchestrator-as-its-own-app phase remains blocked. The orchestrator continues to operate inside this monorepo with a stable boundary and consumer bridge until broader multi-task autonomy proof is achieved.

## Next continuation target

Remain conservative while exercising the bounded supervised two-task pilot:

- continue to refine the pilot admission gate and adjacent-task handoff contract using canary trials
- keep builder/verifier role split explicit and supervised
- keep writing durable canary scorecards and promotion payloads
- only widen scope when artifacts justify the next step
