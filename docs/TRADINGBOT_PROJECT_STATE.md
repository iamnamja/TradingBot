# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–148 are complete in bounded supervised scope plus a narrow one-task autonomous lane.**
- The repo now has deterministic artifacts for the bounded one-task lane: ledger, canary metrics, recovery report, supervised handoff, resume state, scheduler safe-lane policy artifact, and an operator-readable proof bundle.
- Live GitHub hosted-authority interpretation is now more realistic: the repo distinguishes initial reporting delay from genuinely missing required-check evidence and can smoke-prove the `ci-required` contract on a real open PR.

## Honest claim boundary

The repo can now honestly claim:

- one allowlisted safe task at a time can run through the bounded orchestrator lane under supervision
- out-of-lane work is explicitly handed back to supervision instead of widened into broader autonomy
- live GitHub required-check behavior is interpreted conservatively around the stable `ci-required` contract
- operators have a small proof bundle showing what the lane can do and what it still refuses to do

The repo still does **not** honestly claim:

- broad unattended backlog execution
- arbitrary multi-task autonomy
- arbitrary self-hosting control-plane autonomy
- full operator-free overnight scheduling
