# Orchestrator Phase Direction

## Why this document exists

The project has reached the end of the bounded one-task execution-quality proving tranche. That does **not** mean the orchestrator should immediately widen into short chains. This document records the agreed phase order and the explicit gate that must be cleared before any bounded two-task trials begin.

## Agreed priority order

### Phase A — Make one-task autonomous execution actually work
This phase comes first.

The goal is not broader autonomy. The goal is to make the existing bounded one-task lane complete ordinary external-safe tasks with a credible pass rate and with targeted self-heal behavior that materially reduces manual patching.

Phase A now includes these concrete checkpoints:

- canonical external-safe evaluation corpus
- bounded dev / test / repair / controller loop
- external-safe failure taxonomy and narrower self-heal routing
- measurable scoreboarding and recovery artifacts
- external-safe corpus re-proof
- explicit two-task readiness gate

### Phase B — Widen carefully into bounded two-task execution
This phase comes only after Phase A is green.

The goal is to move from one reliable task at a time into very short dependency-aware sequences without losing the conservative stop / requeue / escalation posture.

Phase B is gated by measured one-task evidence, not optimism.

### Phase C — Productize the orchestrator as its own app
This phase comes after execution quality and bounded multi-task reliability exist.

The goal is to wrap a working engine in an operator-facing product rather than to build a shell around an unreliable core.

## Explicit widening gate

Bounded two-task trials are allowed only when the one-task external-safe lane shows all of the following at the same time:

- at least **6** evaluated runs
- at least **0.75** completion rate
- at most **0.25** escalation rate
- at most **0.10** hosted-authority block rate
- at most **0.34** self-healed completion share
- direct completions must exceed self-healed completions

## Current gate result

The current result is **no-go**.

The latest measured re-proof band is still roughly **4 of 6** completed, and **2 of 4** completions still required bounded self-heal. That means the lane is promising, but the evidence still says to keep improving one-task execution quality before starting bounded two-task trials.

## Self-hosting stance

The orchestrator should eventually be able to work on its own app, but that is a later privilege, not the current proving ground.

For now:

- external-safe work remains the primary proving ground
- self-hosting-adjacent work stays supervised or narrowly bounded
- core control-plane self-hosting remains escalation-first until later evidence supports widening

## What this means right now

The next tranche should optimize for:

1. one-task completion rate
2. one-task self-heal quality
3. lower escalation and authority-block frequency
4. more direct completions than self-healed completions
5. continued honesty that the lane is still width-one until the explicit gate clears
