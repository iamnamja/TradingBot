# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 185.

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
- reliability-first import/public compatibility guardrails across benchmark and bounded-corpus entrypoints (Task 182)
- a dedicated reliability benchmark and regression matrix (Task 184)
- an explicit post-185 reliability checkpoint and capability-resume gate (Task 185)

Use `tasks/README.md` as the canonical task-order index, `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative, and `docs/ORCHESTRATOR_CONTRACT_AND_MODEL_COMPAT_186_190.md` as the operator-facing guide for the next tranche.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- a bounded supervised two-task pilot lane is ready and explicitly measured by canary and corpus-backed artifacts
- widening beyond one-task still requires explicit proof, not aspiration
- a post-reliability checkpoint exists with an explicit resume gate verdict

It does not claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Reliability checkpoint and capability-resume gate (Task 185)

- Gate inputs: reliability matrix artifacts under `reliability/` plus existing one-task and two-task pilot artifacts.
- Explicit evaluation categories:
  - recurring failure-family reduction (best-effort delta vs previous where available),
  - retry-count improvement,
  - supervision/intervention rate,
  - compatibility-regression reduction,
  - resume-safe recovery behavior.
- Verdict (conservative): conditionally ready under supervision. A cautious bounded next capability slice may be planned only under supervision and only if reliability metrics remain within the conservative thresholds captured by the checkpoint. Broad unattended multi-task autonomy stays blocked. Standalone productization remains blocked.

## Next continuation target

Stay conservative while fixing recurring contract drift and model-transport mismatch before any new capability widening:

- eliminate repeated README/project-state headline drift with an explicit docs-status consistency guard
- define explicit model profiles and output-transport contracts instead of assuming one file-bundle mode for every model
- add a Codex-compatible patch/apply transport path while preserving the proven GPT file-bundle path
- add provider/model capability negotiation and safe fallback or explicit diagnostics when a selected model cannot satisfy the task transport contract
- record a post-transport checkpoint before resuming any cautious bounded capability widening

### Contract and model-compat tranche note (Tasks 186–190)

This next tranche is still reliability work. It is not broad capability expansion.

The focus is:

- status/narrative consistency validation
- model-profile awareness
- dual transport compatibility (`FILE:/END_FILE` bundle mode and Codex-style patch mode)
- provider/model capability negotiation and safe fallback
- a conservative checkpoint after those contracts are in place
