
# TradingBot and Orchestrator Relationship

## Summary

TradingBot and the orchestrator are related but distinct:

- **TradingBot** is a consumer project with domain-specific runtime, strategies, and tests
- **Orchestrator** is the reusable engineering execution/governance product being prepared for a clearer standalone package boundary

## Current state alignment

- TradingBot remains a supported in-repo consumer
- Orchestrator is productizing inside the monorepo through the multi-agent portability tranche
- The repo is **not** claiming that full standalone extraction is already complete

## Why they remain together now

Keeping both in one repo still supports:

- fast integration feedback
- unified test/harness coverage
- portability hardening while the standalone boundary is being made explicit
- consumer-bridge validation while TradingBot remains the primary in-repo consumer

## Standalone package boundary posture

The orchestrator is being prepared as its own product boundary, but not extracted yet.

Today that boundary is represented by:

- canonical role/contract surfaces under `agents/lib/`
- reusable project/workspace adapter contracts
- consumer bridge requirements for validation commands, acceptance evidence hooks, protected paths, and optional consumer-specific policies
- `agents/run_task.py` as the current shell/entry surface

## Consumer bridge contract

A consumer project must be able to provide, at minimum:

- workspace adapter/config
- validation commands
- acceptance evidence hooks
- protected path declarations
- optional consumer-specific policies

TradingBot satisfies that bridge today, and generic Python workspaces are now a second supported consumer shape.

## Planned evolution

- keep the orchestrator operating correctly inside the monorepo
- continue proving the consumer bridge and portability surfaces
- strengthen the standalone package boundary before any repo split
- treat extraction as future work, not as already complete

## Documentation authority

Canonical narrative docs for this relationship live under `docs/`; root `README.md` is the top-level landing page only.
