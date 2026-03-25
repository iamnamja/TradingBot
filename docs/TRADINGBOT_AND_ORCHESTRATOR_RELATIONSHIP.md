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
- After continuation criteria are met, consider extracting orchestrator into its own repo/package
- Do not treat extraction as already done

## Documentation authority

Canonical narrative docs for this relationship live under `docs/`; root `README.md` is the top-level landing page only.
