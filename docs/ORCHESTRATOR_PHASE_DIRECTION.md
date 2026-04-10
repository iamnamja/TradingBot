# Orchestrator Phase Direction

## Why this document exists

The project has reached the end of the first bounded one-task safe-lane tranche. That was necessary work, but it is easy to lose focus by continuing to add more orchestration surfaces without first making the existing lane truly useful.

This document records the agreed phase order so the project does not drift.

## Agreed priority order

### Phase A — Make one-task autonomous execution actually work
This phase comes first.

The immediate goal is not broader autonomy. The goal is to make the existing bounded one-task lane complete ordinary external-style safe tasks with a credible pass rate and with targeted self-heal behavior that materially reduces manual patching.

Key outcomes for this phase:

- a canonical external-safe evaluation corpus
- a real bounded dev / test / repair / controller loop
- measurable pass-rate and failure-class artifacts
- a supervised reliability re-proof over the external-safe corpus
- an explicit go / no-go gate before any two-task widening

Task 149 is the first checkpoint in this phase: define the manifest and keep the proving ground external-style and safe instead of drifting back into self-hosting-first work.

### Phase B — Widen carefully into bounded multi-task execution
This phase comes only after Phase A is green.

The goal is to move from one reliable task at a time into short dependency-aware sequences without losing the conservative stop / requeue / escalation posture.

Key outcomes for this phase:

- two-task or short-chain bounded trials
- dependency-aware re-entry across more than one task
- queue-level failure containment
- explicit criteria for when to stop widening

### Phase C — Productize the orchestrator as its own app
This phase comes after execution quality and bounded multi-task reliability exist.

The goal is to wrap a working engine in an operator-facing product rather than to build a shell around an unreliable core.

Key outcomes for this phase:

- separate operator-facing app surface
- run history and artifact inspection views
- approvals / escalation UI
- deployment/runtime packaging
- eventually, carefully bounded self-hosting-app work

## Self-hosting stance

The orchestrator should eventually be able to work on its own app, but that is a later privilege, not the first proving ground.

For now:

- external-style safe work is the primary proving ground
- self-hosting-adjacent work stays supervised or narrowly bounded
- core control-plane self-hosting remains escalation-first until later evidence supports widening

## What this means right now

The next tranche should optimize for:

1. one-task execution quality
2. one-task self-heal quality
3. measured pass rate on external-safe corpus
4. only then, explicit readiness criteria for bounded multi-task trials
5. if the gate remains red, remove preventable one-task blockers before any widening

Anything that does not materially improve those four outcomes is lower priority.
