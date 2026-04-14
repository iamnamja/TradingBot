# Task 173 — superseded by 173a and 173b

## Status

Do **not** run this task directly anymore.

Fresh reruns showed that the original Task 173 was still broad enough to pull the agent into `agents.lib.multi_agent_contract`, which remains a high-coupling compatibility surface. The safe continuation path is now split into:

1. `tasks/173a_orchestrator_controller_contract_compatibility_for_bounded_pilot.md`
2. `tasks/173b_orchestrator_supervised_dev_test_role_split_for_bounded_pilot.md`

## Why this task was split

The intended pilot behavior is still the same:

- map pilot `dev` to the existing `builder` role
- map pilot `test` to the existing `verifier` role
- keep `controller` as the only authority for next-role approval
- keep the pilot bounded and supervised

But the original single task kept mixing two jobs:

- restoring/preserving frozen controller-contract compatibility
- adding the bounded supervised pilot role-sequence behavior

Those two jobs should be completed in sequence, not in one run.

## Required execution order

Run these in order:

- `173a` first, to preserve and re-proof the shared controller-contract compatibility surfaces
- `173b` second, to add the bounded supervised dev/test role split additively on top of the preserved surfaces

## What this prevents

This split is intended to prevent the agent from:

- rewriting `agents.lib.multi_agent_contract.py` into a slimmer alternate contract
- changing legacy/public keys or aliases while trying to add pilot behavior
- regressing existing one-task runner, batch-state, package-boundary, and failure-journal callers while working on bounded pilot behavior
