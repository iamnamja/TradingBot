# Task 074b — Orchestrator post-green validation retry loop

## Why this task exists

Once a merge-ready validation profile exists, the orchestrator should not stop at the first post-green failure if the remaining iteration budget can still repair the branch.

The orchestrator should instead treat post-green validation failures as repairable iteration failures when appropriate and continue through the same conservative retry loop it already uses earlier in the run.

## Outcome

Add post-green validation retry handling so the orchestrator can iterate, repair, and re-run the authoritative merge-ready validation profile before claiming final success.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Retryable post-green failure handling

If the merge-ready validation profile fails and iteration budget remains, the orchestrator must:

- classify the failure as a retryable validation-stage failure when appropriate
- continue into another repair iteration
- re-run the merge-ready validation profile after the repair

### 2) Conservative stopping when retries are exhausted

If retries are exhausted or the failure type is not safely repairable, the orchestrator must stop honestly rather than claiming success.

### 3) Visible iteration reason

Runtime output should make it clear that the additional iteration is happening because the final merge-ready validation profile failed, not because an earlier pre-green check failed.

## Tests

Add coverage that proves:

1. a post-green validation failure triggers another repair iteration when retries remain
2. the run stops honestly when retries are exhausted
3. successful repair leads to a final green outcome only after the validation profile passes

## Documentation

Update controls/policies and project-state docs to describe post-green validation retry as part of the autonomous repair loop.

## Guardrails

- Do not create an unbounded retry loop
- Preserve the existing max-iteration cap
- Prefer explicit, conservative stopping over hidden repeated retries

## Acceptance

This task is complete when:

- post-green validation failures can trigger repair iterations
- final success occurs only after the authoritative validation profile passes
- exhausted retry paths stop honestly and visibly
