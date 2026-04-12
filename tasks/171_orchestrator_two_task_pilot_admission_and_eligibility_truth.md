# Task 171 — orchestrator two-task pilot admission and eligibility truth

## Why

Task 170 introduced the bounded two-task pilot gate conceptually. The current runtime already has a conservative gate surface in `agents.lib.task_queue`, but it only checks a promotion verdict, an explicit operator flag, and the hard cap of 2 tasks. Before any bounded pilot work is attempted, that gate must be upgraded into a mechanical eligibility truth surface that reuses the one-task promotion artifact instead of relying on prose judgment.

## Scope

Upgrade the existing Task 170 gate into a durable, threshold-based eligibility truth surface for bounded supervised two-task pilot runs.

## Runtime seams to reuse

- Reuse the existing Task 170 gate helpers in `agents.lib.task_queue` and their wrappers in `agents.run_task`.
- Reuse the promotion artifact already emitted by `src/builder/orchestrator/benchmark_scorecard.py` (`promotion.json` with thresholds, metrics, and verdict).
- Do **not** create a second disconnected pilot-admission subsystem.

## Requirements

- Keep the runtime conservative: ineligible means the bounded two-task pilot remains blocked.
- Extend the Task 170 gate so it can evaluate a structured promotion/admission payload, not just a free-floating verdict string.
- Eligibility must reuse one-task promotion truth already present in the promotion artifact, including at minimum:
  - promotion verdict,
  - supervised or escalation rate,
  - unresolved authority-ambiguity rate,
  - compatibility-regression state.
- Preserve the explicit operator flag requirement and the hard cap of 2 tasks.
- Return threshold reasons explicitly when the pilot is ineligible.
- Persist or return a serializable eligibility artifact that can later be compared to canary benchmark results.
- Do **not** permit general multi-task widening.

## Create or update these exact files
- agents/lib/task_queue.py
- agents/run_task.py
- tests/test_task_queue.py
- tasks/171_orchestrator_two_task_pilot_admission_and_eligibility_truth.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the two-task pilot is declared ineligible when the promotion verdict is below the required level.
- Tests prove the two-task pilot is declared ineligible when supervised-rate or authority-ambiguity thresholds are above the allowed ceiling.
- Tests prove compatibility regressions keep the pilot blocked even when the promotion verdict is otherwise qualifying.
- Tests prove the operator flag and hard cap of 2 remain in force.
- Docs explain that two-task pilot admission is mechanical and conservative, not subjective.
