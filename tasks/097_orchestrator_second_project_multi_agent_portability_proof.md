# Task 097 — Orchestrator second-project multi-agent portability proof

## Why this task exists

Tasks 090–096 create the contracts needed for a broader product, but the orchestrator still needs proof that it can run outside the current repo assumptions.

The next honest milestone is a second-project proof over a simple external Python project shape.

## Outcome

Produce a deterministic second-project portability proof for the multi-agent controller architecture.

## Create or update these exact files

- `tests/test_multi_project_adapters.py`
- `tests/test_project_bootstrap_adapter.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

The proof must demonstrate a simple non-TradingBot Python project where the orchestrator can honestly show:

1. workspace adapter selection
2. bootstrap/setup reasoning
3. builder/verifier/controller role separation
4. dependency-aware task progression over a short manifest
5. truthful stop or continue behavior based on verification authority

## Tests

Add or adjust deterministic local proof tests that demonstrate:

1. a second project/workspace can be bootstrapped through the adapter contract
2. the multi-agent role loop works in that second project shape
3. planner/routing truth remains honest and deterministic
4. docs/README only claim portability to the extent the proof actually covers

## Guardrails

- Keep proof scope narrow and Python-first
- Do not claim arbitrary multi-language portability
- Do not claim broad unattended autonomy
- Treat this as a proof task, not a broad extraction task

## Acceptance

This task is complete when the repo has a deterministic local proof that the multi-agent orchestrator can operate over a simple second project/workspace shape, not just the current repo assumptions.
