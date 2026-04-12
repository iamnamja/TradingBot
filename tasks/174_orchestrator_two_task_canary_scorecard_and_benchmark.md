# Task 174 — orchestrator two-task canary scorecard and benchmark

## Why

We should not widen into a bounded two-task pilot without measurable truth. A small canary benchmark and scorecard must exist before any pilot re-proof can mean anything.

## Scope

Add a bounded two-task canary benchmark and scorecard that can evaluate supervised pilot attempts honestly.

## Requirements

- Extend the existing benchmark truth surfaces rather than creating a disconnected reporting lane.
- Record at least:
  - pilot attempts,
  - pilot completions,
  - blocked admissions,
  - incompatible handoff failures,
  - supervised interventions.
- Keep one-task scorecard truth intact and clearly separate from pilot-specific metrics.
- Produce durable benchmark artifacts suitable for side-by-side comparison.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/174_orchestrator_two_task_canary_scorecard_and_benchmark.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot scorecard persists durable canary metrics.
- Tests prove blocked or ineligible pilot attempts are counted explicitly rather than disappearing into generic failure buckets.
- Docs explain the separation between one-task truth and two-task canary truth.
