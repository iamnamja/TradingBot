# Task 083 — Orchestrator controller contract canonicalization

## Why this task exists

Task 082 proved that the orchestrator can progress through a short ordinary manifest, but it also exposed that controller-facing modules still drift in how they name, map, and persist key controller outcomes.

That drift currently spans:

- `agents/lib/final_acceptance.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/git_workflow.py`
- `agents/lib/failure_journal.py`
- controller-focused tests/docs

Until there is one importable controller contract, the repo can keep passing one layer while silently drifting in another.

## Outcome

Create one canonical controller contract module and make every controller-facing module consume it.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/git_workflow.py`
- `agents/lib/failure_journal.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) One importable contract surface

Introduce a canonical controller-contract module that owns at least:

- controller decision literals / enums / typed aliases
- coercion helpers for controller decisions
- terminal-status to post-task-decision mapping
- merge-posture terminal decision helpers
- canonical persisted field names for controller checkpoints/state
- canonical resume metadata values/helpers

Other controller-facing modules should import from this contract instead of restating ad hoc sets of strings.

### 2) Canonical decision vocabulary

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

### 3) Canonical persisted truth surface

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

### 4) Failure taxonomy alignment

`failure_journal` classification and controller/policy blocking surfaces must stop drifting on similarly named categories across layers.

## Tests

Add or adjust tests that prove:

1. controller layers import and agree on one canonical decision vocabulary
2. batch state/checkpoints persist the canonical truth fields
3. merge-posture decisions are mapped consistently across modules
4. controller/policy failure taxonomy no longer drifts between layers
5. helper wrappers in `agents/run_task.py` continue to expose the canonical contract cleanly

## Guardrails

- Do not broaden scheduler scope
- Do not claim autonomy for protected/controller manifests
- Prefer one explicit contract module over repeated inline string sets
- Keep compatibility wrappers only where they preserve existing tests/entrypoints

## Acceptance

This task is complete when controller-facing modules, persisted state, tests, and docs all use the same canonical controller contract rather than parallel conventions.
