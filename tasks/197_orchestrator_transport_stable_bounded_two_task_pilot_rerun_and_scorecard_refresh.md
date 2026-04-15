# Task 197 — orchestrator transport-stable bounded two-task pilot rerun and scorecard refresh

## Why

The bounded supervised two-task pilot was justified before the transport-recovery work, but it now needs fresh evidence on the recovered runtime path.

## Scope

Rerun the bounded two-task pilot scorecard flow on the recovered runtime path and refresh the conservative scorecard and promotion artifacts.

## Runtime seams to reuse

- Reuse bounded two-task runner and pair-manifest surfaces.
- Reuse canary and bounded-corpus benchmark artifacts.
- Reuse the transport-health artifacts from Tasks 191-195.

## Requirements

- Refresh bounded two-task scorecard artifacts on the recovered runtime path.
- Distinguish transport-stable success from supervision-assisted success explicitly.
- Keep the verdict conservative.
- Preserve the existing curated adjacent-pair corpus discipline.

## Create or update these exact files

- `src/builder/orchestrator/bounded_corpus_benchmark.py`
- `src/builder/orchestrator/benchmark_scorecard.py`
- `tests/test_benchmark_scorecard_integration.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/197_orchestrator_transport_stable_bounded_two_task_pilot_rerun_and_scorecard_refresh.md`

## Non-goals

- Do not widen beyond the bounded supervised two-task pilot.
- Do not add new multi-agent role classes.

## Acceptance criteria

- Refreshed bounded two-task scorecards exist on the recovered runtime path.
- Promotion-style artifacts remain conservative and supervision-aware.
- Tests cover the refreshed scorecard behavior.
