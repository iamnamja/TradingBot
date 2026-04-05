# Task 094 — Orchestrator project workspace adapter and bootstrap contract v2

## Why this task exists

The current hardened proof is still mostly about running tasks in the current repo shape. To become a reusable project builder, the orchestrator needs a stronger project/workspace contract for bootstrapping and validating new or external projects.

## Outcome

Create a project workspace adapter contract that can describe how the orchestrator should bootstrap, validate, and operate within a project that is not already this repo’s current shape.

## Create or update these exact files

- `agents/lib/project_workspace_adapter.py`
- `agents/lib/task_contracts.py`
- `agents/run_task.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_project_bootstrap_adapter.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical workspace contract

Support a project/workspace adapter that can define at least:

- repo/workspace root
- bootstrap/setup commands
- validation commands
- acceptance evidence commands
- protected paths
- artifact/output paths
- merge policy constraints

### 2) New-project bootstrap truth

The orchestrator must be able to reason explicitly about whether a workspace has been bootstrapped successfully or is blocked on environment/setup issues.

### 3) Consumer-specific overrides

TradingBot should remain one consumer, but not the only implied consumer.

### 4) Resume-safe workspace state

Persist enough workspace/bootstrap truth so resume behavior is honest after a partial bootstrap or setup failure.

## Tests

Add or adjust deterministic tests that prove:

1. a non-TradingBot workspace can declare its bootstrap and validation contract
2. bootstrap failures are surfaced as explicit state, not hidden exceptions
3. controller logic can reason over adapter-defined validation commands
4. TradingBot remains a supported consumer adapter rather than a hardcoded assumption

## Guardrails

- Keep the first portability scope Python-first
- Do not promise true multi-language portability yet
- Preserve current strict controller/merge posture rules
- Treat this as a reusable workspace contract, not a broad package extraction task

## Acceptance

This task is complete when the orchestrator can reason explicitly about bootstrapping and validating an external project/workspace through one canonical adapter contract.
