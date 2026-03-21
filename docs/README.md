# TradingBot — Task Backlog

This repository currently contains two related products in one codebase:

- **TradingBot** — the application being built
- **Orchestrator** — the reusable software-delivery engine that is building and hardening the project

## Current state

### TradingBot

TradingBot is at **manual paper-trading readiness**.

### Orchestrator

The orchestrator hardening tranche through **Task 041** is now complete on `main`:

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

## What comes next

The next orchestrator tranche focuses on making the engine more reusable across projects and reducing the cost of future hardening:

- **042** — Harness modularization (split `agents/run_task.py` into reusable modules with no behavior change)
- **043** — Runtime artifact quarantine
- **044** — Spec mode / execution mode workflow
- **045** — Structured failure journal
- **046** — Project bootstrap adapter
- **047** — Verification plugins / validators
- **048** — Safe parallelism

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

## Task order (next tranche)

### Orchestrator productization

- `042_orchestrator_harness_modularization_umbrella` (do not run directly)
- `042a_orchestrator_extract_runtime_foundations`
- `042b_orchestrator_extract_parsers_and_policies`
- `042c_orchestrator_extract_semantic_preflight`
- `042d_orchestrator_thin_run_task_shell_and_parity`
- `043_orchestrator_runtime_artifact_quarantine`
- `044_orchestrator_spec_execution_two_phase_umbrella` (do not run directly)
- `044a_orchestrator_spec_mode_capture`
- `044b_orchestrator_execution_mode_frozen_task`
- `045_orchestrator_failure_journal_and_raw_retry_context`
- `046_orchestrator_project_bootstrap_adapter`
- `047_orchestrator_verification_plugins`
- `048_orchestrator_safe_parallelism`
