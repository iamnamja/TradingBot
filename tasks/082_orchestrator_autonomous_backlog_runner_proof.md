# Task 082 — Orchestrator autonomous backlog runner proof

## Why this task exists

075 proved a short sequential backlog slice. The next milestone is stronger: prove that the orchestrator can take a short ordinary-task manifest and autonomously:

- run a task
- self-heal retryable failures
- enforce final acceptance review
- merge/reset before continuing
- stop honestly when it hits a non-autonomous case

This is the point where “can I feed it a list?” becomes a serious operational question.

## Outcome

Add a narrow, test-backed proof of autonomous backlog progression over a short manifest of ordinary tasks.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `README.md`

## Required behavior

### 1) Accepted-task autonomous progression

Demonstrate that a short ordinary-task manifest can:

- complete one task
- pass authoritative validation and final acceptance
- merge/reset cleanly
- continue to the next task

### 2) Retryable self-heal proof

Include a proof case where one task initially fails in a retryable way, is repaired autonomously, then proceeds to accepted completion.

### 3) Conservative stop proof

Include a proof case where the runner stops honestly on:

- `manual_patch`
- `blocked`
- failed PR/CI/merge posture

### 4) Scope honesty

The proof must stay honest about scope:
- ordinary/non-protected task list first
- deterministic local tests
- not a claim of broad arbitrary-task scheduler autonomy

## Tests

Add E2E-oriented coverage that proves:

1. a short manifest of ordinary tasks can progress task -> accept -> merge/reset -> next task
2. a retryable acceptance failure can self-heal and continue
3. manual/blocked/merge-failure outcomes stop conservatively
4. persisted state and summary artifacts reflect the actual run truthfully

## Documentation

Update project state, product spec, and README to describe the first autonomous backlog-runner proof honestly and conservatively.

## Guardrails

- Do not claim support for arbitrary protected/controller lists
- Keep the proof deterministic and narrow
- Prefer truthful stop conditions over “always continue”
- Preserve the distinction between proof slice and production scheduler

## Acceptance

This task is complete when:

- there is a test-backed proof of short ordinary-task autonomous backlog progression
- self-heal + final acceptance + merge/reset flow is demonstrated honestly
- conservative stop behavior is explicit and test-backed
- docs describe the capability without overstating it
