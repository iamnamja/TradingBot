# Docs Index Addendum

## Current roadmap slice

- `ORCHESTRATOR_ROADMAP_181_185.md` — reliability-first hardening slice after bounded two-task corpus re-proof
- `ORCHESTRATOR_PHASE_DIRECTION.md` — agreed phase order: one-task truth first, bounded two-task pilot second, reliability hardening next, cautious capability widening later, standalone app last
- `ORCHESTRATOR_RELIABILITY_FIRST_181_185.md` — operator-facing rules, artifact expectations, and working cadence for the 181–185 tranche

## Current continuation note

Tasks 157–170 materially strengthened the one-task lane and added a promotion verdict plus an explicit future two-task pilot gate.

Tasks 171–175 completed bounded supervised two-task pilot preparation and re-proof:
- Task 171: two-task pilot admission and eligibility truth
- Task 172: dependency-aware A->B handoff contract
- Task 173a: controller-contract compatibility for bounded pilot
- Task 173b: supervised dev/test role split for bounded pilot
- Task 174: two-task canary scorecard and benchmark artifacts
- Task 175: bounded two-task pilot re-proof and product-direction checkpoint

Tasks 176–180 operationalized the pilot over a real curated corpus and recorded a cautious widening checkpoint:
- Task 176: exact two-task pilot runner and pair-level session ledger
- Task 177: curated adjacent-pair corpus and admission manifest
- Task 178: supervised-intervention artifact and pilot failure digest
- Task 179: real bounded corpus benchmark artifacts under `two_task/bounded_corpus`
- Task 180: bounded two-task corpus re-proof and `bounded_corpus_promotion.json` widening checkpoint

Tasks 181–185 now shift to reliability first:
- Task 181: failure-family taxonomy and repair-target selection
- Task 182: public/import compatibility guardrails for orchestrator benchmark surfaces
- Task 183: resume-safe attempt checkpoint and recovery re-entry truth
- Task 184: reliability benchmark and regression matrix for one-task and bounded two-task runs
- Task 185: reliability checkpoint and explicit gate for when capability widening may resume

## Current next-step note

The near-term focus stays conservative:

- reduce recurring compatibility and task-admission regressions
- improve repair-target precision instead of broad fallback patching
- make interrupted or partially-green runs resume from explicit checkpoints
- measure reliability with retry count, supervision rate, and recurring failure-family evidence
- only consider capability widening after the post-185 reliability gate is satisfied

The immediate operator-facing reference for this slice is `ORCHESTRATOR_RELIABILITY_FIRST_181_185.md`.

## Product-direction checkpoint

- Bounded two-task pilot verdict: ready for a bounded supervised two-task pilot on the curated corpus.
- Reliability-first checkpoint: stabilize runtime behavior and reduce recurring failure families before any new capability tranche.
- Widening checkpoint: cautiously consider widening only after the post-185 reliability gate is satisfied. Broad unattended multi-task autonomy remains blocked. Standalone orchestrator-as-its-own-app remains blocked.

## Reliability-first addition (Task 181)

- New classification and narrow repair-target helpers: agents/lib/repair_targeting.py
- Persisted classification truth for later reuse by repair logic
- Tests: tests/test_repair_targeting.py

These reduce broad repair attempts and reinforce protected and one-task proof surfaces.

## Reliability-first addition (Task 182)

- Explicit import/public compatibility guardrails for orchestrator benchmark surfaces
- Canary and corpus benchmarks remain additive, never mutating strict one-task artifacts
- Tests enforce import stability and artifact-path discipline (POSIX-normalized checks avoid OS-specific regressions)
- Compatibility aliases and explicit exports protect shared import surfaces going forward
