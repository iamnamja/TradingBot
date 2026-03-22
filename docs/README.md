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
- 038a–038c — run loop / CLI / decision logging ✅
- 038d — repo-local import symbol validation ✅
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

The next orchestrator tranche is a **stabilization and portability tranche**, not a new capability tranche.

The main goals are:

- finish shrinking `agents/run_task.py` into a truly thin shell
- freeze the public orchestrator surface
- normalize stale docs/status tables after 042–048
- prove portability with a second non-TradingBot project fixture
- add integrated end-to-end scenarios across the new 043–048 capabilities
- prepare the orchestrator for eventual package/repo extraction

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

## Next task order

### Orchestrator stabilization tranche

- `049_orchestrator_run_task_shell_convergence_umbrella` (do not run directly)
- `049a_orchestrator_run_task_export_and_wrapper_dedupe`
- `049b_orchestrator_run_task_final_shell_routing_extraction`
- `050_orchestrator_public_interface_freeze`
- `051_orchestrator_docs_status_normalization`
- `052_orchestrator_second_project_portability_proof`
- `053_orchestrator_integrated_capabilities_e2e`
- `054_orchestrator_package_extraction_prep`

## Current recommendation

Do **not** switch back to major TradingBot feature expansion yet.

The best next move is to finish the orchestrator stabilization tranche, then either:

1. split/package the orchestrator as its own product, or
2. keep it in-repo but with a frozen public surface

After that, resume TradingBot functional milestones such as recurring execution, reconciliation, reporting, backtesting, and stronger live-mode safety gates.
