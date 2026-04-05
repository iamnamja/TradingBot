# Task 083 — Orchestrator controller contract canonicalization

## Why this task exists

Task 082 proved that the orchestrator can progress through a short ordinary manifest, but it also exposed that controller-facing modules still drift in how they name and persist key controller outcomes.

That drift showed up across:

- `agents/lib/final_acceptance.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/failure_journal.py`
- controller-focused tests/docs

Until this contract is canonical, the orchestrator will keep passing one layer while failing another.

## Outcome

Define and enforce a single canonical controller contract for:

- acceptance decisions
- post-task decisions
- merge-posture failure decisions
- persisted merge/reset truth fields
- resume metadata

## Create or update these exact files

- `agents/lib/final_acceptance.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical decision vocabulary

There must be one controller-wide vocabulary for at least:

Acceptance decisions:

- `accepted`
- `retryable_failure`
- `manual_patch`
- `blocked`

Post-task decisions:

- `continue`
- `stop`
- `manual_patch`
- `blocked`
- `failed_merge`
- `failed_checks`
- `failed_reset`

### 2) Canonical persisted truth surface

Batch state/checkpoints must persist the same controller truth that the executor and resume logic reason over.

At minimum the canonical persisted surface must support:

- terminal status
- acceptance decision
- retry count
- post-task decision
- next-task proceed flag
- accepted-task PR flow completion flag
- required-checks-passed flag
- merged-to-main flag
- clean-main-reset-completed flag
- resume reason
- resume target task path
- resume gate

### 3) Failure taxonomy alignment

`failure_journal` classification for controller/policy surfaces must match the canonical contract and tests. In particular, controller/policy blocking conditions should not drift between similarly named categories across layers.

## Tests

Add/adjust tests that prove:

1. controller layers agree on canonical decision strings
2. batch state/checkpoints persist the canonical truth fields
3. controller/policy failure taxonomy no longer drifts between layers
4. helper wrappers in `agents/run_task.py` continue to expose the canonical contract cleanly

## Guardrails

- Do not broaden scheduler scope
- Do not claim autonomy for protected/controller manifests
- Prefer explicit typed/string contracts over inferred meanings
- Keep compatibility wrappers only where they preserve existing tests/entrypoints

## Acceptance

This task is complete when controller-facing modules, persisted state, tests, and docs all use the same contract vocabulary and truth fields.
