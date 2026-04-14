# Task 181 — orchestrator failure family taxonomy and repair target selection

## Why

Recent task runs show that the orchestrator can sometimes repair the wrong layer, spend retries on compatibility drift rather than the actual task goal, or recover broadly when a narrower repair target would have been sufficient.

The repo now needs an explicit failure-family taxonomy and a narrower repair-target selection surface.

## Scope

Define durable failure-family classification and use it to choose narrower repair targets.

## Runtime seams to reuse

- Reuse current task-admission and exact deliverable-contract enforcement.
- Reuse current subset-preservation and rollback truth where available.
- Reuse existing static-contract and protected-surface checks.
- Reuse bounded one-task and bounded two-task run artifacts as evidence of recurring failure families.

## Requirements

- Introduce a durable taxonomy for recurring orchestrator failure families, including at minimum:
  - task admission / missing exact deliverable contract
  - import / public compatibility surface failure
  - artifact path or artifact shape mismatch
  - benchmark compatibility regression
  - static contract / protected surface violation
  - resume or environment re-entry mismatch
- Persist classification truth in a way later repair logic can reuse.
- Add or harden repair-target selection so these families map to narrower default repair surfaces.
- Keep the behavior conservative:
  - classification should reduce broad repair attempts, not encourage them,
  - protected surfaces and one-task truth surfaces remain respected.

## Create or update these exact files

- `agents/lib/repair_targeting.py`
- `tests/test_repair_targeting.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/181_orchestrator_failure_family_taxonomy_and_repair_target_selection.md`

## Non-goals

- Do not redesign the full orchestrator planner.
- Do not widen capability claims.
- Do not bypass proof-task admission or protected-surface checks.

## Acceptance criteria

- There is an explicit failure-family taxonomy for the recurring orchestrator failures this project has seen recently.
- Repair-target selection maps those families to narrower repair surfaces.
- Tests cover at least one narrow target-selection expectation per major failure family.
- Docs describe the reliability-first reason for this step without overclaiming broader autonomy.

## Implementation notes

- Prefer additive classification and mapping helpers over broad runtime rewrites.
- It is acceptable to default ambiguous failures to a conservative generic family, but the specific families above must be represented explicitly.
