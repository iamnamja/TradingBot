# Task 161 — orchestrator one-task reliability minipack re-proof

## Why

Once Tasks 157–160 land, we need fresh evidence that the one-task lane is materially better, not just more instrumented.

## Scope

Run a small curated reliability minipack and re-measure the one-task lane.

## Requirements

- Use a fixed small set of benchmark-eligible one-task tasks.
- Record results through the integrated strict scorecard.
- Surface the dominant remaining blocker families after the sprint.
- Produce a short re-proof artifact that says whether the one-task lane is improving enough to continue the broader roadmap or needs another reliability sprint.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/161_orchestrator_one_task_reliability_minipack_reproof.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- There is a durable minipack re-proof artifact.
- The artifact includes strict scorecard totals and dominant blocker families.
- Docs/state files are updated to reflect the new measured position after the reliability sprint.
- The output states plainly whether the project should resume the broader roadmap or stay in one-task reliability mode.
