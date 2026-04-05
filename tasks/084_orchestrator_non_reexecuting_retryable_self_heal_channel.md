# Task 084 — Orchestrator non-reexecuting retryable self-heal channel

## Why this task exists

Task 082 required retryable self-heal semantics where the orchestrator repairs a task result and re-evaluates acceptance without re-running the raw task execution for the same attempt.

That behavior must now be made explicit, canonical, and well tested.

## Outcome

Introduce a non-reexecuting retry/self-heal channel so retryable acceptance failures can be repaired deterministically and re-validated without incrementing raw execution attempts.

## Create or update these exact files

- `agents/lib/batch_executor.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/batch_state.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Execution vs repair separation

The controller loop must distinguish between:

- raw task execution attempt
- repair/self-heal transformation of the result
- re-validation + re-acceptance of the repaired result

### 2) No raw re-execution for same retryable attempt

When acceptance is `retryable_failure` and retry budget remains:

- `execute_task` must not be called again for that same item/attempt
- self-heal should receive the failed result and produce a repaired result or patch context
- validator and acceptance review should be rerun on the repaired result

### 3) Persisted truth

Persisted checkpoints/state must make the above behavior auditable, including:

- raw execution attempt count
- retry/self-heal count
- final accepted/not-accepted result
- whether acceptance followed repaired output

## Tests

Add/adjust tests that prove:

1. retryable self-heal can lead to acceptance and continue
2. raw execution count does not increase during repair-only retry
3. repair/self-heal path remains bounded by retry budget
4. persisted state reflects repair count and accepted outcome truthfully

## Guardrails

- Do not introduce hidden infinite retries
- Keep repair behavior deterministic in tests
- Preserve conservative stop posture for manual/blocked/non-retryable cases

## Acceptance

This task is complete when retryable self-heal is explicitly non-reexecuting, persisted truthfully, and proven by tests.
