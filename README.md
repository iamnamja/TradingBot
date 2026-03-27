# TradingBot — Task Backlog

This repository contains two related products in one codebase:

- **TradingBot** — the application being built
- **Orchestrator** — the reusable software-delivery engine that is building and hardening the project

## Current state

### TradingBot

TradingBot is at **manual paper-trading readiness**.

### Orchestrator

The orchestrator productization tranche through **Task 048** is now complete on `main` in substance:

- 031 — real task execution bridge ✅
- 032 — execution result normalization ✅
- 033 — real review and compliance gate ✅
- 034 — branch and worktree guardrails ✅
- 035 — PR creation workflow ✅
- 036 — resume after approval ✅
- 037 — persistent backlog state ✅
- 038a–038d — run loop / CLI / import validation hardening ✅
- 039a–039c — harness hardening tranche ✅
- 040 — end-to-end integration harness ✅
- 041a–041b — multi-project hardening ✅
- 042a–042d — harness modularization tranche ✅
- 043 — runtime artifact quarantine ✅
- 044a–044b — spec / execution two-phase workflow ✅
- 045 — structured failure journal ✅
- 046 — project bootstrap adapter ✅
- 047 — verification plugins / validators ✅
- 048 — safe parallelism ✅

## What comes next

The current orchestrator continuation remains **053–061**.

The immediate focus is still the pre-extraction stabilization path:

- stabilize the seam registry and task-shape enforcement
- finish shrinking `agents/run_task.py` into a thin shell with protected-method discipline
- validate integrated capability flow against current live seams
- finish extraction-prep prerequisites without claiming extraction is already complete

## Important runner conventions

The orchestrator is now strong enough that task quality matters as much as model quality.

Every orchestrator task should continue to include:

- exact method signatures where the API is fragile
- explicit forbidden patterns
- protected-file modes for engine/meta files
- machine-readable contract directives when useful
- acceptance criteria tied to the current real baseline
- narrow scope, ideally one risky production area per task
- clear distinction between task-shape issues, shell issues, and true product/code issues

For **meta harness files** such as `agents/run_task.py`, prefer **one protected method operation per task**. Do not combine a low-cap append operation and a larger replace operation on the same file in one runnable task unless the policies are intentionally compatible.

## Next task order

### Current continuation

- `053_orchestrator_stable_seam_registry`
- `054_orchestrator_task_seam_preflight_linter` **(umbrella only; do not run directly)**
- `054a_orchestrator_meta_harness_lane_gate`
- `054b_orchestrator_bundle_preflight_localized_repair`
- `055_orchestrator_integrated_capabilities_e2e`
- `056_orchestrator_failure_journal_live_seam`
- `057_orchestrator_safe_parallelism_review_integration`
- `058_orchestrator_runtime_artifact_quarantine_integration`
- `059_orchestrator_package_extraction_prep`
- `060_orchestrator_canonical_docs_path_policy`
- `061_orchestrator_task_scope_split_heuristics`

## Current recommendation

Do **not** switch back to major TradingBot feature expansion yet.

The best next move is:

1. merge this task/doc split patch
2. run `054a_orchestrator_meta_harness_lane_gate`
3. merge that result to `main`
4. run `054b_orchestrator_bundle_preflight_localized_repair`
5. then continue to `055`

After the continuation completes, either:

1. split/package the orchestrator as its own product, or
2. keep it in-repo but with a frozen public surface

After that, resume TradingBot functional milestones such as recurring execution, reconciliation, reporting, backtesting, and stronger live-mode safety gates.
