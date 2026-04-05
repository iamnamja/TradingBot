# Task 087 — Orchestrator controller-task strict mode and patch-quality gate

## Why this task exists

The latest controller patches proved that controller-core tasks need stricter handling than ordinary tasks. In particular, low-discipline generated bundles (for example minified or compressed Python that Ruff immediately rejects) should not be applied blindly.

## Outcome

Add a controller-task strict mode that applies stronger validation, focused test ordering, and generated-patch quality checks before accepting a controller-task patch.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/controller_strict_mode.py`
- `agents/lib/task_contracts.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_controller_contract.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `README.md`

## Required behavior

### 1) Controller strict-mode activation

Strict mode must activate when a task touches controller-core files such as:

- `agents/run_task.py`
- `agents/lib/controller_contract.py`
- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/failure_journal.py`
- `agents/lib/git_workflow.py`

### 2) Focused validation order

In strict mode, the lane must:

1. run focused controller tests first
2. reject obvious formatting or discipline failures before apply when possible
3. run full `ruff check .`
4. run full `pytest -q`
5. delay docs/README proof-complete claims until controller proof tests are green

### 3) Patch-quality gate

Before apply, reject bundles with clear bad-patch signals such as:

- large clusters of E701/E702-style one-line statements in core modules
- compressed multi-imports
- obviously suspicious minified formatting in controller files
- mechanically introduced unused-import churn concentrated in touched controller files

## Tests

Add or adjust tests that prove:

1. controller-core task shapes activate strict mode
2. obvious bad controller patch formatting is rejected before apply
3. docs/proof-complete claims are deferred until controller proof tests are green

## Guardrails

- Do not over-block ordinary non-controller tasks
- Keep strict mode transparent in operator messaging
- Prefer deterministic heuristics over vague style judgments
- Keep strict-mode logic in a helper module rather than adding a new blob to `agents/run_task.py`

## Acceptance

This task is complete when controller-core tasks receive stricter pre-apply and post-apply validation, and low-discipline bundles are rejected early.
