# Task 175 — orchestrator bounded two-task pilot re-proof and product checkpoint

## Why

The bounded supervised two-task pilot should only advance if the repo can prove it with real admission, handoff, role-sequence, and canary truth. This is also the right place to make the next product-direction checkpoint explicit so the project does not start productizing an unproven multi-task core.

## Scope

Run the bounded supervised two-task pilot re-proof and record both the pilot verdict and the product-direction checkpoint.

## Requirements

- Use the pilot-admission truth from Task 171, the adjacent-task handoff truth from Task 172, the supervised role-sequence truth from Task 173, and the pilot-canary scorecard from Task 174.
- Produce a durable re-proof artifact that says whether the repo is:
  - not ready for a bounded two-task pilot,
  - conditionally ready under supervision,
  - ready for a bounded supervised two-task pilot.
- Record a concise product checkpoint stating whether the standalone orchestrator-app phase remains blocked or can advance.
- Preserve scope honesty: no claim of broad unattended multi-task autonomy, broad multi-agent autonomy, or orchestrator-as-a-platform unless the proof explicitly justifies it.

## Create or update these exact files
- src/builder/orchestrator/benchmark.py
- src/builder/orchestrator/benchmark_scorecard.py
- tests/test_benchmark_scorecard_integration.py
- tasks/175_orchestrator_bounded_two_task_pilot_reproof_and_product_checkpoint.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- The re-proof artifact contains an explicit bounded-two-task pilot verdict.
- The docs contain an explicit product-direction checkpoint tied to the re-proof result.
- Scope honesty is preserved: broad multi-task autonomy and the separate app phase remain blocked unless the proof says otherwise.
