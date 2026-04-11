# Orchestrator Phase Direction

## Why this document exists

The project has now completed two one-task reliability sprints. The engine is materially stronger than it was before Task 157, but the honest next step is still to improve one-task reliability and promotion truth before widening to bounded multi-task execution.

## Agreed priority order

### Phase A — Make one-task autonomous execution actually work
This phase still comes first.

The immediate goal is not broader autonomy. The immediate goal is to make the existing bounded one-task lane complete ordinary external-style safe tasks with a credible pass rate and with targeted self-heal behavior that materially reduces manual patching.

Key outcomes for this phase:

- a canonical external-safe evaluation corpus
- a real bounded dev / test / repair / controller loop
- measurable pass-rate and failure-class artifacts
- repeated supervised reliability re-proofs over the external-safe corpus or minipack
- an explicit promotion decision before any two-task widening

### Phase B — Widen carefully into bounded multi-task execution
This phase comes only after Phase A is green.

The goal is to move from one reliable task at a time into short dependency-aware sequences without losing the conservative stop / requeue / escalation posture.

### Phase C — Productize the orchestrator as its own app
This phase comes after execution quality and bounded multi-task reliability exist.

The goal is to wrap a working engine in an operator-facing product rather than to build a shell around an unreliable core.

## What this means right now

The next tranche should optimize for:

1. one-task scorecard truth
2. one-task authority corroboration
3. measured elimination of the dominant remaining one-task failure family
4. an explicit promotion verdict before any default-path or two-task pilot decision
