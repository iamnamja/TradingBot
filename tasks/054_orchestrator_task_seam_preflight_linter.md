# Task 054 — Orchestrator Task / Seam Preflight Linter Umbrella

## Goal

This is a **sequencing umbrella** for the task / seam preflight hardening work.

Do **not** run this task directly.

The original combined scope on `agents/run_task.py` mixed:

- a narrow meta-harness lane gate change
- a broader `request_and_parse_bundle` preflight / localized-repair change

That shape created unnecessary protected-file policy conflicts on a large meta
file. The work is now split into two runnable subtasks.

## Subtask order

1. `054a_orchestrator_meta_harness_lane_gate`
2. `054b_orchestrator_bundle_preflight_localized_repair`

Merge `054a` to `main` before running `054b`.

## Why the split exists

For core meta harness files such as `agents/run_task.py`, the preferred pattern is:

- one protected method operation per runnable task
- narrow, deterministic tests
- explicit preservation of the live shell/export contract

This umbrella exists to preserve continuity in the roadmap while directing
execution to the safer split tasks above.
