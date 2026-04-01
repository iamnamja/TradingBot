# Task 074a — Orchestrator merge-ready validation profile

## Why this task exists

Recent backlog-continuation tasks have repeatedly reached an internal "green" state inside the orchestrator loop, but still required manual cleanup afterward because the final branch was not yet merge-ready under the same commands the operator runs locally.

Before adding the first user-facing batch runner CLI, the orchestrator needs a single authoritative merge-ready validation profile and must use that profile itself before claiming success.

## Outcome

Add an explicit merge-ready validation profile and make the orchestrator run it after a nominal green pass, before declaring the task complete.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Authoritative merge-ready validation profile

Define a narrow authoritative validation profile that matches the intended local merge-readiness checks for autonomous task completion.

At minimum, the profile must cover:

- `ruff check .`
- `pytest -q`

The implementation may also preserve narrower targeted checks earlier in the loop, but final success must depend on the authoritative merge-ready validation profile.

### 2) Post-green validation gate

After the orchestrator believes a task is green, it must run the authoritative merge-ready validation profile before reporting success.

If the profile fails, the run must not declare success or push as completed.

### 3) Honest failure classification

When the post-green validation profile fails, the failure must be surfaced as a validation-stage failure rather than silently treating the task as complete.

## Tests

Add coverage that proves:

1. the authoritative merge-ready validation profile is invoked before final success
2. a post-green validation failure prevents the task from being marked complete
3. the validation failure is surfaced clearly in runtime output/state

## Documentation

Update controls/policies and project-state docs to state that autonomous success now depends on the same merge-ready validation profile the operator expects, not only on intermediate loop checks.

## Guardrails

- Do not add broad CI orchestration here
- Keep the profile local, deterministic, and grounded in the current repo workflow
- Preserve earlier targeted checks where they help convergence, but do not let them replace the final merge-ready gate

## Acceptance

This task is complete when:

- the orchestrator runs an explicit authoritative merge-ready validation profile before success
- failure in that profile prevents the task from being considered complete
- runtime/tests/docs reflect the new gate honestly
