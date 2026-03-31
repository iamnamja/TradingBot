# Task 071a — Orchestrator user-facing runtime artifact retention switch

## Why this task exists

Task 070b added internal retention support for known-safe runtime artifacts such as:

- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

However, in live operator use there is still no clear surfaced control to keep those files after a successful `--push` run. Successful pushed runs still quarantine/remove them by default, which makes the retention capability hard to access in practice.

This task finishes that work by exposing an explicit operator-facing retention switch while preserving the default quarantine safety behavior.

## Requirements

Implement a narrow follow-up that:

1. keeps current default behavior unchanged:
   - successful `--push` runs still quarantine known-safe runtime artifacts before commit unless retention is explicitly requested
2. exposes a user-facing retention control through:
   - CLI flag: `--keep-runtime-artifacts`
   - environment variable: `TRADINGBOT_KEEP_RUNTIME_ARTIFACTS=1`
3. treats either control as enabling retention for known-safe runtime artifacts
4. when retention is enabled:
   - keep `_last_agent_model_output.txt`
   - keep `_last_agent_file_bundle.txt`
   - ensure those files are still unstaged / not committed automatically
5. prints explicit lifecycle messaging so the operator can tell whether runtime artifacts were:
   - retained
   - quarantined and removed
   - or blocked due to unknown runtime artifacts
6. preserves current unknown-artifact blocking behavior

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/artifact_quarantine.py`
- `tests/test_artifact_quarantine.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Implementation guidance

- Thread the CLI flag and env var into the existing runtime-artifact quarantine decision path instead of duplicating logic.
- Prefer a single boolean such as `keep_runtime_artifacts` or similar that is computed once and passed into quarantine handling.
- Keep the change narrow; do not redesign batch state, queueing, or controller sequencing here.

## Acceptance criteria

- Running the orchestrator without the new control preserves the current default quarantine behavior.
- Running with `--keep-runtime-artifacts` keeps known-safe `_last_agent_*` files in the working tree after a successful pushed run.
- Running with `TRADINGBOT_KEEP_RUNTIME_ARTIFACTS=1` also keeps known-safe `_last_agent_*` files in the working tree after a successful pushed run.
- Retained known-safe runtime artifacts remain unstaged and are not committed automatically.
- Unknown runtime artifacts still block or warn exactly as current policy requires.
- `ruff check .` passes.
- `pytest -q` passes.
