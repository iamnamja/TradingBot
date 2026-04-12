# Task 174 — orchestrator two-task canary scorecard and benchmark

## Why

A bounded two-task pilot should not be widened on intuition alone. The repo already has a durable one-task benchmark and promotion surface in `benchmark.py` and `benchmark_scorecard.py`. The bounded pilot should extend that benchmark system with canary truth instead of creating a disconnected reporting lane.

## Scope

Add a bounded two-task canary benchmark and scorecard that can evaluate supervised pilot attempts honestly.

## Runtime seams to reuse

- Reuse the existing benchmark session artifact directory structure.
- Reuse the integrated scorecard and promotion-artifact style already present in `src/builder/orchestrator/benchmark_scorecard.py`.
- Keep one-task scorecard truth intact and clearly separate from two-task canary truth.

## Requirements

- Extend the existing benchmark truth surfaces rather than creating a disconnected pilot-reporting lane.
- Record at minimum:
  - pilot attempts,
  - pilot completions,
  - blocked admissions,
  - handoff-incomplete or handoff-incompatible failures,
  - supervised interventions.
- Ineligible pilot attempts must be counted explicitly, not disappear into generic failure buckets.
- Keep the existing one-task scorecard and promotion artifact compatible for the already-proven lane.
- Produce durable canary artifacts that are suitable for later comparison by Task 175.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/174_orchestrator_two_task_canary_scorecard_and_benchmark.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot scorecard persists durable canary metrics.
- Tests prove blocked or ineligible pilot attempts are counted explicitly rather than disappearing into a generic failed bucket.
- Tests prove the one-task scorecard surface remains intact for the already-proven lane.
- Docs explain the separation between one-task truth and bounded two-task canary truth.
