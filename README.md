# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through **Task 170**.

The repo can now honestly claim a materially hardened **one-task lane** with:

- proof-task admission gating on exact deliverable contracts
- strict no-manual-intervention benchmark scoring
- deliverable-contract and completion-integrity enforcement
- authority corroboration and conservative run truth
- empty-bundle retry shaping and durable transport diagnostics
- runtime-artifact hygiene and subset-preservation normalization
- a threshold-based promotion artifact for the one-task lane
- a defined default-path posture for eligible one-task work and an explicit future two-task pilot gate

Use `tasks/README.md` as the canonical task-order index and `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- widening beyond one-task still requires explicit proof, not aspiration
- a bounded future two-task pilot is defined conceptually, but not yet proven operationally

It does **not** claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Next continuation target

Shift from one-task promotion truth into **bounded two-task pilot preparation under supervision**:

- mechanize the explicit two-task pilot admission gate
- make dependency handoff between adjacent tasks explicit and durable
- split the existing builder/verifier roles explicitly for bounded supervised pilot work
- measure the pilot with a real canary scorecard on the same benchmark lane
- only then decide whether a bounded supervised two-task pilot is justified
