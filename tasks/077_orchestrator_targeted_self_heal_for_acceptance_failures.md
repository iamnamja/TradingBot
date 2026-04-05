# Task 077 — Orchestrator targeted self-heal for acceptance failures

## Why this task exists

074b added retry behavior for post-green validation failures, but the orchestrator still needs a more explicit way to classify and repair **final acceptance** failures such as:

- required file missing from committed `HEAD`
- required file only present in working tree
- unexpected tracked artifact in branch diff
- authoritative validation profile failure after a nominal green pass

Without that, the controller still tends to oscillate between “green” and manual cleanup.

## Outcome

Teach the orchestrator to classify final-acceptance failures into a small retryable taxonomy and generate focused self-heal repair prompts rather than generic reruns.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Final-acceptance failure taxonomy

At minimum, distinguish:

- `missing_required_in_head`
- `required_only_in_worktree`
- `unexpected_tracked_artifact`
- `merge_ready_validation_failed`

### 2) Retryability classification

For each class above, decide whether it is:

- safely retryable autonomously
- manual-patch only
- blocked

### 3) Focused self-heal request shape

When retryable, generate a focused repair request that names:

- the acceptance failure class
- the missing/extra files involved
- whether the task must modify committed `HEAD`, clean working tree state, or remove unexpected tracked artifacts

### 4) Bounded loop behavior

Preserve the existing bounded retry budget. Do not create unbounded self-heal loops.

## Tests

Add coverage that proves:

1. each acceptance failure class is recognized correctly
2. retryable cases produce a focused repair prompt/context
3. non-retryable/manual cases do not masquerade as autonomous fixes
4. bounded retry posture remains intact

## Documentation

Update controls/policies and project state docs to describe final-acceptance self-heal behavior and its explicit conservative limits.

## Guardrails

- Prefer narrow, file-specific repair prompts over broad reruns
- Do not treat protected/controller breakages as ordinary retryable cleanup
- Preserve truthful stop reasons when autonomous repair is exhausted or unsafe

## Acceptance

This task is complete when:

- final-acceptance failures are classified explicitly
- retryable acceptance failures can generate focused self-heal repair context
- non-retryable cases stop honestly
- tests cover the taxonomy and bounded behavior
- docs reflect the new behavior honestly
