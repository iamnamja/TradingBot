# Task 155 — Orchestrator safe lint preflight normalization

## Goal
Reduce preventable one-task external-safe failures by converting isolated lint/formatting breakage on required Python paths into a bounded automatic normalization pass before the run is recorded as failed.

## Why this task exists
Task 154 added the explicit go / no-go gate for bounded two-task trials and the repo remains in **no-go** posture. The current measured corpus still contains a preventable lint-only non-completion. Before widening the lane, the orchestrator should remove that ordinary friction in the narrowest safe way possible.

## Scope
- bounded one-task lane only
- external-safe admitted work only
- Python required paths only
- no broad code rewriting and no widened autonomy claims
- keep self-hosting and protected/control-plane work out of scope

## Create or update these exact files
- `agents/run_single_task.py`
- `agents/lib/safe_lint_preflight.py`
- `tests/test_single_task_runner.py`
- `tests/test_safe_lint_preflight.py`
- `tasks/155_orchestrator_safe_lint_preflight_normalization.md`
- `tasks/README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/ORCHESTRATOR_PHASE_DIRECTION.md`
- `docs/ORCHESTRATOR_ROADMAP_155_160.md`
- `docs/README.md`
- `docs/NEW_CHAT_HANDOFF_PROMPT.md`

## Required behavior
When the bounded one-task verifier isolates a failure to lint/formatting and the task only implicates required Python paths inside the safe lane, the runner should be able to:
- plan a safe lint-normalization pass
- run a bounded normalization sequence on the required Python paths only
- replay lint and the minimal remaining validation commands
- record whether that bounded preflight succeeded
- convert the run into a truthful completion only if the replayed validation turns green

Non-lint failures must remain unchanged, and the task must not claim that the repo is ready for two-task trials.

## Acceptance
This task is complete when lint-only failures on admitted external-safe Python work can be normalized inside the bounded one-task lane, with tests proving both the successful normalization path and the unchanged failure posture when normalization is not applicable or does not converge.
