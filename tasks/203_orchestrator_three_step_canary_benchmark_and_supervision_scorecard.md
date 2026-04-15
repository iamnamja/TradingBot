# Task 203 — orchestrator three-step canary benchmark and supervision scorecard

## Why

After Tasks 201-202, the repo still will not have durable widening proof unless the three-step canary path is benchmarked honestly. Supervision truth must remain first-class so operator help never gets mistaken for autonomous success.

## Scope

Benchmark the supervised three-step canary path and persist a supervision-aware scorecard.

## Runtime seams to reuse

- Reuse the exact three-step canary runner from Task 201.
- Reuse the curated chain corpus from Task 202.
- Reuse scorecard vocabulary from one-task and bounded two-task artifacts:
  - direct progress,
  - supervision-assisted progress,
  - blocked admission,
  - handoff failure,
  - manual intervention observed.
- Reuse current session directory and artifact naming discipline where possible.

## Requirements

- Add a durable benchmark entrypoint for the three-step canary corpus.
- Persist scorecard artifacts that distinguish at minimum:
  - direct supervised-canary completion,
  - supervision-assisted chain completion,
  - blocked admission,
  - adjacency or handoff failure,
  - resume/re-entry degradation,
  - manual intervention observed.
- Keep supervision truth explicit and benchmark-visible.
- Keep one-task and bounded two-task truth surfaces unchanged.

## Create or update these exact files

- `src/builder/orchestrator/three_step_canary_benchmark.py`
- `tests/test_three_step_canary_benchmark.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/203_orchestrator_three_step_canary_benchmark_and_supervision_scorecard.md`

## Non-goals

- Do not replace the existing one-task or bounded two-task scorecards.
- Do not widen to arbitrary multi-task benchmarking.

## Acceptance criteria

- Tests prove the real three-step canary runner is invoked by the benchmark.
- Tests prove durable benchmark and scorecard artifacts are written.
- Tests prove direct progress and supervision-assisted progress remain distinguishable.
- Tests prove one-task and bounded two-task truth surfaces remain untouched.
