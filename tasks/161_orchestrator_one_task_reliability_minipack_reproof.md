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

## Implementation notes

- A curated minipack is embedded in the benchmark harness under `MINIPACK_ONE_TASK_ITEMS`.
- The external-safe harness writes:
  - per-task JSON trials
  - a session.json
  - a strict `scorecard.json` + compatible `scoreboard.json`
  - a durable `reproof.json` with:
    - strict scorecard totals
    - a simple dominant-blocker-family histogram
    - an explicit go/no-go decision
- The decision rule is conservative:
  - insufficient samples → `insufficient_data`
  - any manual invalidation or pass rate < 0.60 → `stay_in_one_task_reliability_mode`
  - otherwise → `resume_broader_roadmap`

## How to run locally (operator checklist)

- Choose an external-safe one-task executor callable.
- Invoke:
  - Python API: `run_reliability_minipack_reproof(executor=...)`
  - or run individual tasks via `run_one_task_external_safe_benchmark(...)`
- Inspect artifacts under `artifacts/benchmark/sessions/<session_id>/`:
  - `scorecard.json` (strict, durable)
  - `scoreboard.json` (compat surface)
  - `reproof.json` (decision + blocker families)

## Minipack seed (fixed IDs)

- one_task_docs_fix_minimal
- one_task_tests_guardrail_update
- one_task_code_small_refactor
- one_task_lint_normalization
- one_task_runtime_artifact_quarantine

These IDs are stable handles for curated, benchmark-eligible one-task items.

## Expected output discipline

- Keep artifact paths stable and machine-readable.
- Avoid runtime artifact sprawl.
- Keep the decision posture conservative and operator-auditable.
