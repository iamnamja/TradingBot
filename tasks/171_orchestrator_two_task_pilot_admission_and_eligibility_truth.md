# Task 171 — orchestrator two-task pilot admission and eligibility truth

## Why

Task 170 defined a two-task pilot gate conceptually. We now need a mechanical admission truth surface so the repo can decide, based on explicit conditions, whether a bounded supervised two-task pilot is even eligible to be attempted.

## Scope

Add a durable admission/eligibility truth for bounded two-task pilot runs.

## Requirements

- Reuse the promotion verdict and one-task scorecard truth rather than inventing a disconnected lane.
- Define explicit eligibility conditions for a two-task pilot, including at minimum:
  - one-task promotion verdict,
  - recent authority ambiguity rate,
  - recent supervised/escalation rate,
  - compatibility seam regression status.
- Persist a durable pilot-eligibility artifact suitable for later benchmark comparison.
- Keep the runtime conservative: ineligible means the two-task pilot remains blocked.

## Create or update these exact files
- agents/run_task.py
- agents/lib/task_queue.py
- tests/test_task_queue.py
- tasks/171_orchestrator_two_task_pilot_admission_and_eligibility_truth.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the two-task pilot can be declared ineligible for explicit threshold reasons.
- Tests prove the pilot cannot be marked eligible if the one-task promotion verdict is below the required level.
- Docs explain that pilot admission is mechanical and conservative, not subjective.
