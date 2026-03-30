# TradingBot and Orchestrator Relationship

## Summary

TradingBot and the orchestrator are related but distinct:

- **TradingBot** is the domain system (strategy, risk, execution, paper cycle)
- **Orchestrator** is the engineering execution/governance system used to implement and harden work safely

## Current state alignment

- TradingBot remains at **manual paper-trading readiness**
- Orchestrator has completed 042–048 and 049–052
- Orchestrator is currently in the 053–061 hardening / integration continuation
- Orchestrator is reusable and productizing, but still in-repo

## Why they remain together now

Keeping both in one repo currently supports:

- fast integration feedback
- unified test/harness coverage
- seam stabilization while interfaces converge
- portability hardening while extraction preconditions are still being proven

## Planned evolution

- Continue through 053–061
- Progress through deferred continuation tasks 062–068, including extraction preparation work
- Stabilize package boundaries and package-level orchestrator surface before any repository split
- After continuation criteria are met, execute a planned extraction sequence (documented under `docs/orchestrator_extraction_plan.md`)
- Do not treat extraction as already done

## Boundary and import contract

- `builder.orchestrator` is the orchestrator package namespace.
- TradingBot code remains under `tradingbot.*` and is not part of the orchestrator package API.
- Package-level re-exports from `builder.orchestrator` should remain orchestrator-focused (config + adapter contracts), not TradingBot-facing.
- Existing module-level orchestrator imports remain valid for compatibility during prep and migration sequencing.

## Documentation authority

Canonical narrative docs for this relationship live under `docs/`; root `README.md` is the top-level landing page only.
