# Task 180 — orchestrator bounded two-task corpus re-proof and widening checkpoint

## Why

Once the real bounded two-task pilot runner has been exercised over a curated pair corpus, the repo needs another honest checkpoint: should it continue the bounded supervised two-task pilot as-is, widen cautiously, or remain blocked from any broader step?

## Scope

Run a corpus-backed bounded two-task re-proof and record a conservative widening checkpoint.

## Runtime seams to reuse

- Reuse the exact bounded two-task pilot runner from Task 176.
- Reuse the curated adjacent-pair corpus from Task 177.
- Reuse the supervised-intervention and failure-digest truth from Task 178.
- Reuse the real bounded corpus benchmark artifacts from Task 179.
- Reuse the existing benchmark/promotion artifact style already present in the repo.

## Requirements

- Use the real bounded pilot evidence from Tasks 176–179.
- Produce a durable verdict that says whether the repo is:
  - not ready to continue the bounded pilot,
  - conditionally ready under supervision,
  - ready to continue the bounded supervised two-task pilot on the curated pair corpus,
  - or cautiously ready to expand the curated pair corpus while staying supervised.
- Record an explicit widening checkpoint that states what remains blocked.
- Keep the verdict conservative:
  - broad multi-task autonomy remains blocked unless the evidence explicitly justifies a later tranche,
  - standalone productization remains blocked.
- Reuse the benchmark/promotion artifact style already present in the repo.
- Keep one-task truth surfaces unchanged.
- Keep the existing Task 179 bounded corpus benchmark entrypoint additive; do not replace the one-task or canary benchmark compatibility surfaces.

## Artifact expectations

- Treat the Task 179 bounded corpus benchmark outputs as the evidence source.
- Add a durable bounded-corpus promotion/checkpoint artifact alongside the bounded corpus benchmark outputs.
- The widening checkpoint must explicitly state:
  - the bounded two-task corpus verdict,
  - whether the curated corpus may widen while staying supervised,
  - that broad unattended multi-task autonomy remains blocked,
  - that standalone orchestrator productization remains blocked.

## Create or update these exact files

- `src/builder/orchestrator/bounded_corpus_benchmark.py`
- `tests/test_benchmark_scorecard_integration.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/180_orchestrator_bounded_two_task_corpus_reproof_and_widening_checkpoint.md`

## Non-goals

- Do not claim broad autonomous multi-task readiness.
- Do not unblock the standalone orchestrator product.
- Do not skip from bounded two-task corpus evidence directly to arbitrary scheduling.
- Do not redesign or replace the one-task benchmark compatibility surface.
- Do not redesign or replace the bounded two-task canary compatibility surface.

## Acceptance criteria

- The re-proof artifact contains an explicit bounded-two-task corpus verdict.
- The bounded corpus benchmark path writes a durable promotion/checkpoint artifact for the corpus evidence.
- Docs record an explicit widening checkpoint and what remains blocked.
- Scope honesty is preserved: broader autonomy and product extraction remain blocked unless the evidence clearly justifies the next step.
- `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md` do not overclaim broad multi-task autonomy or standalone orchestrator product readiness.

## Implementation notes

- The bounded-corpus benchmark entrypoint remains additive: `builder.orchestrator.bounded_corpus_benchmark.run_bounded_two_task_corpus_benchmark(...)`.
- The corpus benchmark persists its own session directory at `two_task/bounded_corpus/`.
- A durable promotion/checkpoint artifact named `bounded_corpus_promotion.json` is written alongside `pairs.json` and `summary.json`.
- The promotion artifact includes:
  - `verdict` (conservative),
  - `thresholds` (explicit),
  - `metrics` (derived from the corpus run),
  - `widening_checkpoint` (explicitly stating that broad unattended multi-task autonomy and standalone productization remain blocked).
