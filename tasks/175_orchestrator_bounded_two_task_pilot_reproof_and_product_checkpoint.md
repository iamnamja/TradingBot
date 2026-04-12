# Task 175 — orchestrator bounded two-task pilot re-proof and product checkpoint

## Why

Before the repo can honestly widen beyond the one-task default path or move toward productizing the orchestrator as a separate app, it needs one explicit checkpoint: do Tasks 171–174 justify a bounded supervised two-task pilot, and what does that imply for product direction?

## Scope

Run a bounded two-task pilot re-proof and record both the pilot verdict and the product-direction checkpoint.

## Requirements

- Use the admission, handoff, role-split, and canary truth from Tasks 171–174.
- Produce a durable verdict that says whether the repo is:
  - not ready for a bounded two-task pilot,
  - conditionally ready under supervision,
  - ready for a bounded supervised two-task pilot.
- Record an explicit product checkpoint stating whether the standalone orchestrator-as-its-own-app phase remains blocked.
- The verdict must remain conservative: broad multi-task autonomy and app-platform claims stay blocked unless the proof explicitly justifies the next widening step.
- Reuse the benchmark/promotion artifact style already present in the repo rather than inventing a new checkpoint format.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- README.md
- tasks/175_orchestrator_bounded_two_task_pilot_reproof_and_product_checkpoint.md
- docs/TRADINGBOT_PROJECT_STATE.md
- docs/README.md

## Acceptance criteria

- The re-proof artifact contains an explicit bounded-two-task pilot verdict.
- The docs contain an explicit product-direction checkpoint.
- The root README does not overclaim broad multi-task autonomy or a finished standalone orchestrator product.
- Scope honesty is preserved: broad multi-task autonomy and the separate app phase remain blocked unless the proof says otherwise.
