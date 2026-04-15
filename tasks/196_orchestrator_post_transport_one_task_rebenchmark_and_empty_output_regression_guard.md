# Task 196 — orchestrator post-transport one-task rebenchmark and empty-output regression guard

## Why

Tasks 191-195 recovered the runner from the empty-output black-box problem.

The repo now needs fresh one-task evidence on the recovered runtime path and a durable guard so empty-output failures do not quietly regress the default proving lane.

## Scope

Refresh one-task benchmark evidence on the recovered runtime path and add an explicit empty-output regression guard.

## Runtime seams to reuse

- Reuse one-task benchmark scoring from the existing benchmark and scorecard surfaces.
- Reuse transport-health and capture-integrity artifacts from Tasks 191-195.
- Reuse conservative promotion and regression-guard style from earlier one-task checkpoints.

## Requirements

- Produce refreshed one-task benchmark artifacts on the recovered runtime path.
- Persist a small regression guard that fails the refreshed one-task verdict if empty-output failures reappear above the tolerated threshold.
- Keep the proven GPT file-bundle path as the baseline.
- Keep the result conservative and supervision-aware.

## Create or update these exact files

- `src/builder/orchestrator/benchmark.py`
- `src/builder/orchestrator/benchmark_scorecard.py`
- `tests/test_benchmark_scorecard_integration.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/196_orchestrator_post_transport_one_task_rebenchmark_and_empty_output_regression_guard.md`

## Non-goals

- Do not widen multi-task autonomy claims.
- Do not change provider selection defaults.
- Do not hide regressions behind softer transport parsing.

## Acceptance criteria

- One-task benchmark artifacts are refreshed on the recovered runtime path.
- Empty-output regressions are evaluated explicitly in the refreshed one-task verdict.
- Tests cover the new guard behavior.

## Implementation notes

- The one-task benchmark harness now wires the strict scorecard writer directly into the live session flow and persists `scorecard.json`, `scoreboard.json`, and `promotion.json`.
- An explicit empty-output regression guard persists `promotion_guard.json` and degrades `promotion.json` to `not_ready` when the observed empty-output rate exceeds a small tolerated threshold.
- The two-task canary harness writes additive `canary_*` artifacts without touching the strict one-task benchmark surface.
