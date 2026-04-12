# Orchestrator Phase Direction

## Why this document exists

The project has now completed the one-task reliability and promotion tranche through Task 170. The repo is materially stronger than it was at Task 157, but the honest next move is still careful, bounded widening rather than broad autonomy claims.

## Agreed priority order

### Phase A — Keep one-task execution truthful and stable
This remains the base layer.

The one-task lane is now conditionally ready under supervision, but its scorecard and promotion truth must remain the authoritative gate for any future widening.

### Phase B — Prepare a bounded supervised two-task pilot
This is the current next phase.

The goal is not arbitrary multi-task execution. The goal is to prove the smallest credible adjacent two-task pilot with:

- mechanical pilot admission,
- deterministic task handoff,
- explicit supervised dev/test role separation,
- and durable canary scorecard truth.

### Phase C — Productize the orchestrator as its own app
This phase still comes later.

The orchestrator should only be wrapped in a separate operator-facing product after bounded two-task pilot truth exists. Building an app shell around a not-yet-proven multi-task core would still be premature.

## What this means right now

Optimize the next tranche for:

1. two-task pilot admission truth
2. adjacent-task handoff truth
3. supervised dev/test role split in the pilot lane
4. measured two-task canary truth
5. a bounded two-task pilot re-proof before any broader product claim
