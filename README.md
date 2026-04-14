# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 182.

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

Use `tasks/README.md` as the canonical task-order index, `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative, and `docs/ORCHESTRATOR_RELIABILITY_FIRST_181_185.md` as the operator-facing guide for the next tranche.

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

Stay conservative while keeping the scope fixed and improving runtime reliability first:

- stabilize failure-family classification and repair-target selection so the orchestrator patches the right surface more often
- harden import, benchmark, and public compatibility contracts so additive benchmark work stops regressing shared surfaces
- persist resume-safe attempt state and recovery checkpoints so interrupted or partially-green runs can re-enter precisely
- benchmark bounded one-task and two-task reliability by failure family, retry count, and supervision rate
- only reopen capability widening after the reliability checkpoint shows lower intervention and fewer recurring compatibility failures

### Reliability-first hardening note (Task 181)

A durable orchestrator failure-family taxonomy and a conservative repair-target selection map have been added:

- Code: agents/lib/repair_targeting.py
- Tests: tests/test_repair_targeting.py

The taxonomy classifies recurring failures (admission, import/public surface, artifact path/shape, benchmark compatibility, protected/static contract, and resume/re-entry) and maps them to narrow default repair surfaces. The behavior reduces broad repair attempts and preserves protected and one-task proof surfaces.

### Reliability-first hardening note (Task 182)

Import/public surface guardrails were added for orchestrator benchmark and bounded-corpus entrypoints:

- One-task benchmark preserves strict scorecard and promotion artifacts.
- Two-task canary benchmark writes only `canary_*` artifacts and does not modify strict one-task artifacts.
- Bounded-corpus benchmark remains additive and writes only under `two_task/bounded_corpus/`.
- Tests enforce import stability and artifact-path discipline across OSes using POSIX-normalized checks.
- Compatibility aliases and explicit exports are preferred to preserve import/public surfaces.

### Reliability-first hardening note (Task 183)

Resume-safe attempt checkpoints and conservative re-entry truth were added:

- Code: agents/lib/resume_state.py, agents/lib/attempt_state.py
- Tests: tests/test_attempt_state_resume.py

Behavior:

- Records explicit checkpoints that capture last safe transition and intended re-entry surface.
- Distinguishes fresh execution, retry after failure, resume after partial progress, and manual intervention before resume.
- When state is ambiguous or unsafe, defaults to a safe restart instead of optimistic resume.
