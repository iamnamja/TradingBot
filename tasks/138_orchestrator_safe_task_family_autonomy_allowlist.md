# Task 138 — Orchestrator safe task-family autonomy allowlist

## Goal
Introduce an explicit admission lane for autonomous single-task runs so the orchestrator can safely run allowlisted ordinary tasks while self-hosting control-plane work remains escalation-first by default.

## Scope
- task-family admission and controller posture
- allowlisted ordinary implementation / test / docs work only
- explicit escalation or block posture for protected self-hosting harness work

## Create or update these exact files
- `agents/lib/task_contracts.py`
- `agents/lib/controller_contract.py`
- `agents/run_task.py`
- `tests/test_run_task_contract_directives.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/README.md`

## Required behavior
The admission lane should classify whether a task is autonomous-safe, supervised-only, or escalation-required. Ordinary tasks may enter the safe lane; self-hosting control-plane tasks touching core orchestrator harness files should not be silently attempted by default. The decision and rationale should be explicit and testable.

## Acceptance
This task is complete when the repo has a deterministic allowlisted admission lane for autonomous single-task runs, unsafe self-hosting work is escalated conservatively, and the docs clearly describe the safe-lane boundary.
