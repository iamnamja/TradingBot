# Task 084 — Orchestrator non-reexecuting retryable self-heal channel

## Why this task exists

Task 082 proved the desired behavior: a retryable acceptance failure can be repaired and re-evaluated without re-running raw task execution for the same attempt.

That behavior now needs to be made explicit, canonical, and auditable in persisted controller truth.

## Outcome

Introduce a non-reexecuting retry/self-heal channel so retryable acceptance failures are repaired deterministically and re-validated without incrementing raw execution attempts.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/final_acceptance.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Explicit execution vs repair separation

The controller loop must distinguish between:

- raw task execution attempt
- repair/self-heal transformation of the result
- re-validation + re-acceptance of the repaired result

### 2) No raw re-execution for the same retryable attempt

When acceptance is `retryable_failure` and retry budget remains:

- `execute_task` must not be called again for that same item/attempt
- self-heal should receive the failed result and produce a repaired result or patch context
- validator and acceptance review should be rerun on the repaired result

### 3) Canonical persisted audit fields

Persisted checkpoints/state must make the above behavior auditable with explicit fields, including at least:

- `execution_attempt_count`
- `repair_count`
- `accepted_after_repair`

Do not overload a single ambiguous counter to mean both raw execution and repair loops.

## Tests

Add or adjust tests that prove:

1. retryable self-heal can lead to acceptance and continue
2. raw execution count does not increase during repair-only retry
3. repair/self-heal path remains bounded by retry budget
4. persisted state reflects execution-vs-repair truth explicitly and consistently

## Guardrails

- Do not introduce hidden infinite retries
- Keep repair behavior deterministic in tests
- Preserve conservative stop posture for manual/blocked/non-retryable cases

## Acceptance

This task is complete when retryable self-heal is explicitly non-reexecuting, persisted truthfully, and proven by tests using separate execution and repair truth fields.
