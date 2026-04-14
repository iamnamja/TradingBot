# Orchestrator Phase Direction

## Why this document exists

The project now has:

- a supervised, measured one-task default lane,
- a bounded supervised two-task pilot lane with canary and real corpus artifacts,
- and a completed reliability-first tranche through Task 185.

The honest next move is still not broad autonomy. The next move is to remove recurring contract drift before capability widening resumes.

## Agreed priority order

### Phase A — Keep one-task execution truthful and stable
This remains the base layer.

The one-task lane is conditionally ready under supervision, and its benchmark/promotion truth remains authoritative.

### Phase B — Prove a bounded supervised two-task pilot
This phase is complete enough to operate conservatively.

The goal was never arbitrary scheduling. The goal was a measured adjacent-task pilot with explicit admission, handoff, supervised role split, and durable artifacts.

### Phase C — Reliability-first hardening
This phase is now complete through Task 185.

The repo added:

- failure-family targeting,
- benchmark/public-surface compatibility guardrails,
- resume-safe attempt checkpoints,
- a reliability benchmark,
- and a post-185 capability-resume gate.

### Phase D — Contract and model-compatibility hardening
This is the current next phase.

The repo now needs to eliminate two recurring contract failures before any new widening:

- repeated docs/status headline drift across `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md`
- model/output-transport mismatch, especially Codex-style model output versus the current strict `FILE:/END_FILE` bundle contract

The goal is not broad capability yet. The goal is to make the runtime and narrative contracts more explicit and less fragile.

### Phase E — Cautious bounded capability widening
This comes only after the contract/model layer is materially more stable.

Any widening remains bounded, supervised, and backed by explicit checkpoint evidence.

### Phase F — Standalone orchestrator productization
This still comes later.

The orchestrator should only be wrapped as its own operator-facing app after broader multi-task proof exists and the runtime contracts are stable enough to support it.
