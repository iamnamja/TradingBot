# Task 171 — orchestrator two-task pilot admission and eligibility truth

## Why

Task 170 introduced the bounded two-task pilot gate conceptually and the runtime already has a minimal readiness-gate surface. The next step is to make pilot admission mechanical, threshold-based, and durable enough to audit without widening execution yet.

## Scope

Tighten the existing bounded two-task gate into an explicit eligibility-truth surface for supervised pilot admission only.

## Starting point in the current repo

The current runtime already exposes a minimal gate snapshot and evaluation surface through `agents.lib.task_queue` and `agents.run_task`. Build on that surface instead of inventing a second admission lane.

## Requirements

- Reuse the existing promotion verdict and one-task scorecard truth rather than creating a disconnected pilot-readiness system.
- Keep `two_task_readiness_gate_snapshot(...)` as the policy snapshot surface and extend it with explicit threshold/configuration fields for pilot eligibility.
- Extend the current evaluation surface so it returns a deterministic, JSON-serializable pilot-eligibility artifact with stable keys for later comparison.
- The eligibility artifact must capture, at minimum:
  - promotion verdict,
  - recent authority ambiguity rate,
  - recent supervised or escalation rate,
  - compatibility seam regression status,
  - explicit operator pilot flag truth,
  - final eligibility verdict,
  - reason codes for any ineligible result.
- Ineligible must remain the conservative default. This task does not authorize pilot execution; it only establishes truthful admission logic.
- Re-export the tightened surface through `agents.run_task` so current public/runtime compatibility remains intact.

## Create or update these exact files
- agents/run_task.py
- agents/lib/task_queue.py
- tests/test_task_queue.py
- tasks/171_orchestrator_two_task_pilot_admission_and_eligibility_truth.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove the pilot can be declared ineligible for explicit threshold reasons rather than a generic rejection.
- Tests prove the pilot cannot be marked eligible when the one-task promotion verdict is below the required level.
- Tests prove the returned eligibility artifact is stable, inspectable, and JSON-serializable.
- Docs explain that bounded two-task pilot admission is mechanical and conservative, not subjective.
