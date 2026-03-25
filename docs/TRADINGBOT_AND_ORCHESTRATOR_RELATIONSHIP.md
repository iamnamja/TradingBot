# TradingBot and Orchestrator Relationship

## Summary

TradingBot and the orchestrator are related but distinct:

- **TradingBot** is the domain system (strategy, risk, execution, paper cycle).
- **Orchestrator** is the engineering execution/governance system used to implement and harden work safely.

## Current state alignment

- TradingBot remains at **manual paper-trading readiness**.
- Orchestrator has completed 042–048 and is now in 049–054 stabilization.
- Orchestrator is reusable and productizing, but still in-repo.

## Why they remain together now

Keeping both in one repo currently supports:

- fast integration feedback
- unified test/harness coverage
- portability hardening while interfaces stabilize

## Planned evolution

- Continue stabilization through 049–054.
- After stabilization criteria are met, consider extracting orchestrator into its own repo/package.
- Do not treat extraction as already done.

## Documentation authority

Canonical narrative docs for this relationship live under `docs/`; root `README.md` is the top-level landing page only.
