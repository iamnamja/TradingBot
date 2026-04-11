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

## Orchestrator wiring

The benchmark harness now integrates a strict scorecard and emits a durable promotion artifact:

- src/builder/orchestrator/benchmark_scorecard.py
  - Writes scorecard.json and scoreboard.json.
  - Computes a promotion verdict using explicit PromotionThresholds.
  - Persists promotion.json with thresholds, metrics, and verdict.
- src/builder/orchestrator/benchmark.py
  - Wires the strict scorecard into the live benchmark session and persists the promotion verdict.

## Default thresholds

The default thresholds encoded in PromotionThresholds are:

- min_pass_rate: 0.60
- min_direct_minus_self_healed_margin: 0.20
- max_supervised_rate: 0.10
- max_authority_ambiguity_rate: 0.05
- require_no_compat_regressions: True

These thresholds are recorded in each promotion.json for durability and auditability.

## Durable promotion artifact

Each benchmark session directory now contains a promotion.json file with:

- created_at: ISO-8601 timestamp
- thresholds: the exact numeric thresholds applied
- metrics: total_runs, successes, failures, pass_rate, direct_rate, self_healed_rate, supervised_rate, authority_ambiguity_rate, invalidated_rate
- compatibility_regressions_detected: boolean
- verdict: one of:
  - not_ready
  - conditionally_ready_under_supervision
  - ready_to_be_default

## Current promotion decision (post-Tasks 166–168)

Based on the integrated scorecard and the encoded thresholds, the promotion artifact decides readiness per session deterministically:

- Sessions with strong pass rate, materially higher direct vs self-healed rate, and low supervision/authority-ambiguity achieve: ready_to_be_default.
- Sessions with high pass rate but without a material direct-over-self-heal margin or with slightly elevated supervision rates achieve: conditionally_ready_under_supervision.
- Sessions failing the pass-rate threshold or invalidated by manual intervention remain: not_ready.

No widening to two-task execution was introduced by this task. The artifact is purely evaluative and only informs whether one-task autonomous runs should be the default proving path for the curated, benchmark-eligible set.
