# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 190.

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
- reliability-first import/public compatibility guardrails across benchmark and bounded-corpus entrypoints
- docs-status headline consistency guarding
- explicit model-profile declaration, dual-transport support, provider/model capability negotiation, and a conservative contract/model transport checkpoint through Task 190

Use `tasks/README.md` as the canonical task-order index, `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative, and `docs/ORCHESTRATOR_TRANSPORT_STABILITY_AND_OBSERVABILITY_191_195.md` as the operator-facing guide for the next tranche.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- a bounded supervised two-task pilot lane is ready and explicitly measured by canary and corpus-backed artifacts
- docs status consistency is guarded
- model profiles and transport contracts are explicit
- protected-method and bundle transport failures are now diagnosable enough to justify a focused observability tranche
- widening beyond the current bounded scope still requires proof, not aspiration

It does not claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- fully reliable protected-method transport under automation
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Contract/model transport checkpoint (Task 190)

- Checkpoint verdict: conditionally ready under supervision.
- Meaning: a cautious bounded next slice may be planned only if it is aimed at stabilizing transport behavior and observability rather than widening autonomy.
- Blocked areas remain explicit: broad unattended multi-task autonomy and standalone productization stay blocked.

## Active tranche

Current active tranche: 191-195.

## Next continuation target

Stay conservative and focus on runner stability and fast observability:

- make raw model-output capture non-empty or explicitly diagnosable on every transport failure
- add durable transport-failure artifacts that explain exactly what parser path and contract were attempted
- make protected-method transport preflight and fallback behavior explicit before expensive retries
- benchmark transport health and recurring failure families over real runs
- only reopen any next capability slice after transport stability is measurably improved
