# Task 169 — orchestrator one-task promotion re-proof

## Why

We need a formal decision point for whether the orchestrator’s one-task lane is strong enough to become the default way we attempt the next external-safe tasks.

## Scope

Re-run the benchmark or minipack proof after Tasks 166–168 and produce a promotion verdict for the bounded one-task lane.

## Requirements

- Re-run the benchmark or fixed reliability minipack against the curated one-task external-safe set.
- Produce a durable promotion artifact that states whether the one-task lane is:
  - not ready,
  - conditionally ready under supervision,
  - ready to become the default path for benchmark-eligible one-task work.
- Base the verdict on explicit thresholds, not prose judgment alone.
- This task must not widen to two-task execution; it only decides whether one-task autonomous runs should become the default proving path.

## Suggested thresholds

Use concrete metrics in this spirit:

- strong overall one-task completion rate,
- direct-completion rate materially better than self-healed-only completion rate,
- low supervised or escalation rate,
- low unresolved authority-ambiguity rate,
- no recurring compatibility seam regressions in the benchmark set.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/169_orchestrator_one_task_promotion_reproof.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- There is a durable promotion artifact with explicit thresholds and a verdict.
- Docs are updated to reflect the current promotion outcome.
- If the verdict is “not ready,” docs clearly say what still blocks promotion.
