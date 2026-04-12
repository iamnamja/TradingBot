# Task 174 — orchestrator two-task canary scorecard and benchmark

## Why

The repo should not widen into a bounded supervised two-task pilot without measurable truth. A small pilot-canary scorecard must exist so blocked admission, bad handoff, and supervised intervention show up explicitly instead of disappearing into generic failure buckets.

## Scope

Add a bounded supervised two-task canary benchmark and scorecard that extends the current benchmark truth surfaces without polluting one-task promotion truth.

## Requirements

- Extend the existing benchmark and benchmark-scorecard surfaces rather than creating a disconnected pilot-reporting lane.
- Keep one-task scorecard and promotion truth intact and clearly separate from pilot-canary truth.
- Record at minimum these pilot metrics:
  - pilot attempts,
  - pilot completions,
  - blocked admissions,
  - incompatible handoff failures,
  - supervised interventions.
- The resulting pilot-canary artifact must be durable and suitable for side-by-side comparison with later re-proofs.
- Do not allow blocked or ineligible pilot attempts to disappear into generic failure totals.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/174_orchestrator_two_task_canary_scorecard_and_benchmark.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot scorecard persists durable canary metrics with explicit pilot-specific fields.
- Tests prove blocked or ineligible pilot attempts are counted explicitly rather than merged into generic failure buckets.
- Docs explain the separation between one-task truth and two-task pilot-canary truth.
