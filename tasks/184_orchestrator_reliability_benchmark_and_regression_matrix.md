# Task 184 — orchestrator reliability benchmark and regression matrix

## Why

The repo now has promotion and pilot artifacts, but it still lacks a dedicated reliability view that measures retry count, supervision rate, and recurring failure families across one-task and bounded two-task work.

## Scope

Create a reliability benchmark and regression matrix that measures runtime stability directly.

## Runtime seams to reuse

- Reuse one-task benchmark artifacts.
- Reuse bounded two-task canary artifacts.
- Reuse bounded corpus benchmark artifacts.
- Reuse failure-family classification from Task 181 if available.
- Reuse supervised-intervention truth and pair-level ledger truth where available.

## Requirements

- Produce a reliability-oriented artifact or artifact set that captures at least:
  - task/run count
  - retry count to green
  - recurring failure-family counts
  - supervision/intervention rate
  - admission-block frequency
  - compatibility-regression frequency when detectable
- Cover both one-task and bounded two-task contexts, even if the metrics differ slightly by lane.
- Keep the artifact additive and separate from the existing promotion artifacts.
- Add tests that verify the reliability matrix persists expected fields and does not overwrite existing one-task or two-task truth surfaces.

## Create or update these exact files

- `src/builder/orchestrator/reliability_benchmark.py`
- `tests/test_reliability_benchmark.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/184_orchestrator_reliability_benchmark_and_regression_matrix.md`

## Non-goals

- Do not replace current promotion artifacts.
- Do not reinterpret the bounded-corpus promotion artifact as a reliability artifact.
- Do not widen capability claims.

## Acceptance criteria

- A durable reliability benchmark or regression-matrix artifact is written.
- The artifact includes retry and intervention-oriented metrics, not just success metrics.
- Existing benchmark and promotion artifacts remain unchanged.
- Docs record this as a reliability measurement step.

## Implementation notes

- Favor a dedicated reliability artifact path and naming convention over overloading existing benchmark files.
