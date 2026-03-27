# TradingBot — Task Backlog

This repository contains two related products in one codebase:

- **TradingBot** — the application being built
- **Orchestrator** — the reusable software-delivery engine that is building and hardening the project

## Current state

### TradingBot

TradingBot is at **manual paper-trading readiness**.

### Orchestrator

The orchestrator productization tranche through **Task 052** is complete on `main`, and the early continuation hardening steps through **Task 054** are now also complete in substance:

- 031 — real task execution bridge ✅
- 032 — execution result normalization ✅
- 033 — real review and compliance gate ✅
- 034 — branch and worktree guardrails ✅
- 035 — PR creation workflow ✅
- 036 — resume after approval ✅
- 037 — persistent backlog state ✅
- 038a–038d — run loop / CLI / decision logging / import validation ✅
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
- 049 — run-task shell convergence umbrella ✅
- 049a — run-task export / wrapper dedupe ✅
- 049b — final shell routing extraction ✅
- 050 — public interface freeze ✅
- 051 — docs/status normalization ✅
- 052 — second-project portability proof ✅
- 053 — stable seam registry ✅
- 054a — meta harness lane gate ✅
- 054b — bundle preflight / localized repair ✅

## What comes next

The current continuation is now focused on **integration stabilization and extraction readiness**, not new feature expansion.

The main goals are:

- validate a seam-aligned integrated end-to-end scenario across the 043–054 capabilities
- stabilize the remaining focused seam families individually
- document extraction prerequisites and canonical docs placement
- teach the orchestrator when a task should be split across seam families

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

The orchestrator is now strong enough that task quality matters as much as model quality.

Every orchestrator task should continue to include:

- exact method signatures where the API is fragile
- explicit forbidden patterns
- protected-file modes for engine/meta files
- machine-readable contract directives when useful
- acceptance criteria tied to the current real baseline
- narrow scope, ideally one risky production area per task
- clear distinction between task-shape issues, shell issues, and true product/code issues
- split subtasks when a single task would combine multiple seam families or conflicting protected-file policies

## Next task order

### Orchestrator continuation / extraction-readiness tranche

- `055_orchestrator_integrated_capabilities_e2e`
- `056_orchestrator_failure_journal_live_seam`
- `057_orchestrator_safe_parallelism_review_integration`
- `058_orchestrator_runtime_artifact_quarantine_integration`
- `059_orchestrator_package_extraction_prep`
- `060_orchestrator_canonical_docs_path_policy`
- `061_orchestrator_task_scope_and_split_heuristics`

## Current recommendation

Do **not** switch back to major TradingBot feature expansion yet.

The best next move is to finish the current orchestrator continuation and then either:

1. split/package the orchestrator as its own product, or
2. keep it in-repo with a frozen public surface and explicit extraction-readiness docs

After that, resume TradingBot functional milestones such as recurring execution, reconciliation, reporting, backtesting, and stronger live-mode safety gates.
