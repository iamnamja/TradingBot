# TradingBot Project State

## Current phase

TradingBot is in a **manual paper-trading readiness** phase.

## What this means

- Focus is on controlled, supervised paper execution workflows.
- Risk/execution/strategy plumbing is exercised in paper mode.
- This is not a claim of autonomous production live-trading readiness.

## Relationship to orchestrator progress

- Orchestrator hardening through 042–048 is complete.
- Current orchestrator stabilization tranche is 049–054.
- These orchestrator advances improve engineering reliability and velocity, but do not change TradingBot’s declared operational phase.

## Repo and docs posture

- TradingBot and orchestrator remain co-located during stabilization.
- Recommended separation (orchestrator extraction) is deferred until after tranche 049–054 completion.
- Canonical narrative status docs are maintained under `docs/`, with root `README.md` as entry point.
