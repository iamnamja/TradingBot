# TradingBot — Task Backlog

This repository contains two related products in one codebase:

- **TradingBot** — the application being built
- **Orchestrator** — the reusable software-delivery engine that is building and hardening the project

## Current state

### TradingBot

TradingBot is at **manual paper-trading readiness**.

### Orchestrator

The orchestrator hardening baseline through **Task 048** is complete on `main` in substance, and the early stabilization tasks **049–052** are also complete on `main`.

## What comes next

The next orchestrator sequence is a **hardening-first continuation tranche**, not a new product-capability tranche.

The main goals are:

- make orchestrator testing seams explicit and stable
- add task/seam preflight checks so bad bundles fail earlier
- validate one integrated capability flow without tightening optional seams
- stabilize failure-journal, safe-parallelism/review, and runtime-quarantine seam families independently
- finish package extraction prep
- codify canonical docs placement and future task-splitting heuristics

## Repo conventions

- Source layout:
  - `src/tradingbot/...` — trading application
  - `src/builder/orchestrator/...` — reusable orchestrator engine
  - `agents/...` — task-running harness and agent glue code
- Tests: `tests/...`
- CI target remains:
  - `ruff check .`
  - `pytest -q`

## Important runner conventions

The orchestrator is now strong enough that task quality and seam clarity matter as much as model quality.

Every orchestrator task should continue to include:

- exact method signatures where the API is fragile
- explicit forbidden patterns
- protected-file modes for engine/meta files
- machine-readable contract directives when useful
- acceptance criteria tied to the current real baseline
- narrow scope, ideally one seam family per task
- clear distinction between:
  - task-shape issues
  - shell/runner issues
  - true product/code issues

## Next task order

### Completed on main

- `049_orchestrator_run_task_shell_convergence_umbrella` (umbrella, not run directly)
- `049a_orchestrator_run_task_export_and_wrapper_dedupe`
- `049b_orchestrator_run_task_final_shell_routing_extraction`
- `050_orchestrator_public_interface_freeze`
- `051_orchestrator_docs_status_normalization`
- `052_orchestrator_second_project_portability_proof`

### Current hardening / integration continuation

- `053_orchestrator_stable_seam_registry`
- `054_orchestrator_task_seam_preflight_linter`
- `055_orchestrator_integrated_capabilities_e2e`
- `056_orchestrator_failure_journal_live_seam`
- `057_orchestrator_safe_parallelism_review_integration`
- `058_orchestrator_runtime_artifact_quarantine_integration`
- `059_orchestrator_package_extraction_prep`
- `060_orchestrator_canonical_docs_path_policy`
- `061_orchestrator_task_scope_and_split_heuristics`

## Current recommendation

Do **not** switch back to major TradingBot feature expansion yet.

The best next move is to finish the orchestrator hardening / integration continuation, then either:

1. split/package the orchestrator as its own product, or
2. keep it in-repo but with a stable seam registry, preflight checks, and an explicitly frozen public surface

After that, resume TradingBot functional milestones such as recurring execution, reconciliation, reporting, backtesting, and stronger live-mode safety gates.
