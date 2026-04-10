# Task 160 — orchestrator one-task promotion re-proof

## Why

We need a formal decision point for whether the orchestrator’s one-task lane is strong enough to become the default way we attempt the next external-safe tasks.

## Scope

Re-run the benchmark harness after Tasks 156–159 and produce a promotion verdict for the bounded one-task lane.

## Requirements

- Re-run the benchmark harness against the curated one-task external-safe set.
- Produce a promotion artifact that states whether the one-task lane is:
  - not ready,
  - conditionally ready under supervision,
  - ready to become the default path for benchmark-eligible one-task work.
- The promotion verdict must be based on explicit thresholds, not prose judgment alone.
- The promotion task must not widen to two-task execution; it only decides whether one-task autonomous runs should become our default proving path.

## Suggested thresholds

These thresholds may be refined by the implementation, but the task should use concrete metrics in this spirit:

- strong overall one-task benchmark completion rate,
- direct completion rate materially better than self-healed-only completion rate,
- low supervised/escalation rate,
- low unresolved authority ambiguity rate,
- no recurring compatibility seam regressions in the benchmark set.

## Acceptance criteria

- There is a durable promotion artifact with explicit thresholds and a verdict.
- Docs are updated to reflect the current promotion outcome.
- If the verdict is “not ready,” docs clearly say what still blocks promotion.
