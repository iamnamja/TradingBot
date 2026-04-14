# Task 179 — orchestrator real bounded two-task corpus benchmark

## Why

Tasks 174–175 established a canary benchmark and a conservative pilot verdict, but the repo now needs to exercise the real bounded pilot runner against the curated pair corpus so the next checkpoint is based on real pilot executions rather than synthetic or placeholder results.

## Scope

Benchmark the real bounded supervised two-task pilot runner over the curated adjacent-pair corpus.

## Runtime seams to reuse

- Reuse the exact two-task runner from Task 176.
- Reuse the curated pair manifest from Task 177.
- Reuse the supervised-intervention and failure-digest truth from Task 178.
- Reuse the benchmark session directory conventions and `canary_*` artifact style from Tasks 174–175.

## Requirements

- Run the curated adjacent-pair corpus through the real bounded two-task runner.
- Persist durable benchmark artifacts that are still clearly separated from the one-task truth surfaces.
- Benchmark output must reflect:
  - total pair attempts,
  - eligible/ineligible pairs,
  - completed bounded pilot pairs,
  - blocked admissions,
  - handoff failures,
  - supervised interventions.
- The benchmark must use the real bounded two-task runner rather than synthetic direct counters.
- Keep the one-task `scorecard.json`, `scoreboard.json`, and `promotion.json` unchanged.

## Non-goals

- Do not benchmark arbitrary multi-task chains.
- Do not widen beyond curated real two-task pairs.

## Acceptance criteria

- Tests prove the real bounded pilot runner is invoked by the corpus benchmark.
- Tests prove durable benchmark artifacts are written for the real pair corpus.
- Tests prove one-task truth surfaces remain untouched.
