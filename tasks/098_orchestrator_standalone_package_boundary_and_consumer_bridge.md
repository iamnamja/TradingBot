# Task 098 — Orchestrator standalone package boundary and consumer bridge

## Why this task exists

The orchestrator currently lives inside the TradingBot monorepo, but the product goal is broader than TradingBot. Before any full extraction, the repo needs an explicit standalone package boundary and a documented consumer bridge so TradingBot is just one consumer rather than the implied identity of the product.

## Outcome

Create a stronger standalone package boundary and consumer bridge posture without fully extracting the orchestrator yet.

## Create or update these exact files

- `agents/lib/multi_agent_contract.py`
- `agents/lib/project_workspace_adapter.py`
- `agents/run_task.py`
- `tests/test_orchestrator_package_surface.py`
- `docs/TRADINGBOT_AND_ORCHESTRATOR_RELATIONSHIP.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Explicit product boundary

Make it clearer what belongs to the reusable orchestrator product versus what belongs to a consumer project such as TradingBot.

### 2) Consumer bridge contract

Document and test the minimal bridge a consumer project must provide, including:

- workspace adapter/config
- validation commands
- acceptance evidence hooks
- protected path declarations
- optional consumer-specific policies

### 3) No premature extraction claim

This task should improve the boundary, not pretend that full standalone extraction is already complete.

### 4) Compatibility for the current monorepo

TradingBot must remain a supported consumer while the product boundary becomes clearer.

## Tests

Add or adjust tests that prove:

1. the public orchestrator surface is still stable for a consumer project
2. consumer-specific configuration can be isolated from the reusable orchestrator surface
3. the repo can document a clearer extraction path without breaking the current monorepo flow

## Guardrails

- Do not claim the orchestrator is already fully extracted
- Keep current monorepo consumers working
- Prefer explicit boundary docs/tests over sweeping package surgery in one task
- Treat this as extraction prep, not a repo split

## Acceptance

This task is complete when the orchestrator has a clearer standalone package boundary and consumer bridge, while still operating correctly inside the current monorepo.
