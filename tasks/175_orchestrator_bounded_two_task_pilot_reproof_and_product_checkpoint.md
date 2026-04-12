# Task 175 — orchestrator bounded two-task pilot re-proof and product checkpoint

## Why

Before we invest in a broader multi-task lane or start productizing the orchestrator as a separate app, we need one explicit checkpoint: is a bounded supervised two-task pilot actually justified, and what does that imply for product direction?

## Scope

Run a bounded two-task pilot re-proof and record both the pilot verdict and the product-direction checkpoint.

## Requirements

- Use the pilot admission, handoff, role-split, and canary scorecard truth from Tasks 171–174.
- Produce a durable verdict that says whether the repo is:
  - not ready for a bounded two-task pilot,
  - conditionally ready under supervision,
  - ready for a bounded supervised two-task pilot.
- Record a short product checkpoint explaining whether the standalone orchestrator app phase should remain blocked.
- Do not claim general multi-task or app-platform autonomy unless the proof actually justifies it.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/175_orchestrator_bounded_two_task_pilot_reproof_and_product_checkpoint.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- The re-proof artifact contains an explicit bounded-two-task pilot verdict.
- The docs contain an explicit product-direction checkpoint.
- Scope honesty is preserved: broad multi-task autonomy and the separate app phase remain blocked unless the proof says otherwise.
