# Task 179 — orchestrator real bounded two-task corpus benchmark

## Why

Tasks 174–178 established the canary benchmark, the exact bounded two-task runner, the curated adjacent-pair manifest, and durable supervision/failure truth. The next step is to benchmark the **real bounded pilot runner** over the curated pair corpus without regressing the already-proven one-task and canary compatibility surfaces.

## Scope

Add the real bounded supervised two-task corpus benchmark **additively** on top of the current benchmark module.

## Runtime seams to reuse

- Reuse the exact two-task runner from Task 176: `agents.lib.bounded_pilot.run_bounded_two_task_pilot`.
- Reuse the curated pair manifest from Task 177 via the current manifest helpers in `agents.lib.pair_manifest`.
- Reuse the supervised-intervention and failure-digest truth from Task 178 when counting supervised intervention / failure outcomes.
- Reuse the existing benchmark session directory conventions and the existing `canary_*` artifact style for two-task artifacts.

## Current compatibility constraints that must remain untouched

The repo already has live compatibility surfaces for:

- `builder.orchestrator.benchmark.run_one_task_external_safe_benchmark`
- `builder.orchestrator.benchmark.run_two_task_canary_benchmark`
- `builder.orchestrator.benchmark_scorecard.BenchmarkSession`
- the existing live-scorecard wiring inside `src/builder/orchestrator/benchmark.py`

This task must preserve those surfaces exactly.

## Requirements

- Add a real bounded corpus benchmark entrypoint without replacing or reimplementing the existing one-task strict benchmark or existing two-task canary benchmark behavior.
- Run the curated adjacent-pair corpus through the real bounded two-task runner.
- If a helper adapter is needed, it must adapt to the Task 176 runner that already exists; do **not** invent or import a nonexistent `builder.orchestrator.runner.run_bounded_two_task_pair` contract.
- Keep one-task `scorecard.json`, `scoreboard.json`, and `promotion.json` behavior unchanged.
- Keep current canary artifact names and current canary metric meanings unchanged for the existing canary benchmark.
- Persist durable artifacts for the real bounded pair corpus that are clearly separated from one-task truth surfaces.
- Benchmark output must reflect:
  - total pair attempts,
  - eligible/ineligible pairs,
  - completed bounded pilot pairs,
  - blocked admissions,
  - handoff failures,
  - supervised interventions.
- The benchmark must use the real bounded two-task runner rather than synthetic direct counters.

## Non-goals

- Do not rewrite the existing benchmark scorecard session implementation.
- Do not replace the current one-task strict benchmark wrapper.
- Do not replace the current two-task canary wrapper.
- Do not widen beyond curated real two-task pairs.
- Do not introduce new broad multi-task runner abstractions.

## Acceptance criteria

- Tests prove the real bounded pilot runner is invoked by the corpus benchmark.
- Tests prove durable benchmark artifacts are written for the real pair corpus.
- Tests prove one-task truth surfaces remain untouched.
- Tests prove the existing canary benchmark compatibility surface remains untouched.
- Static contracts remain green without introducing imports of missing symbols from `builder.orchestrator.runner`.
