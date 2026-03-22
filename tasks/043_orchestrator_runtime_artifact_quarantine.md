# Task 043 — Runtime Artifact Quarantine

## Goal

Continue shrinking `agents/run_task.py` by extracting runtime artifact quarantine logic into a reusable helper module while preserving the current shell behavior.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/artifact_quarantine.py`
- `agents/run_task.py`
- `tests/test_runtime_artifact_quarantine.py`
- `ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

All listed files must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD REPLACE_METHOD=_cleanup_runtime_artifacts_for_commit
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_artifact_quarantine_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

This task must preserve the current shell behavior.

The purpose is to **move artifact-quarantine policy into `agents/lib/artifact_quarantine.py`** and keep `agents/run_task.py` as a thin delegator.

Do not change:
- branch naming behavior
- retry limits
- approval behavior
- current CLI contract

## Current shell / CLI guidance

If tests invoke `agents.run_task.main()`, they must target the **current** shell surface.

Specifically:

- Do **not** assume `main(argv)` unless it actually exists
- Do **not** assume legacy flags like `--task` or `--non-interactive` unless they actually exist
- If invoking `main()`, monkeypatch `sys.argv` and use the current positional `task` plus existing optional flags only

## Required behavior

Known safe artifacts should be auto-unstaged and deleted before final commit/push when recoverable, while still being surfaced in warnings/audit output.

Examples of known safe artifacts include:

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

Unknown artifacts must still fail or block as policy requires.

## Test requirements

Add deterministic tests for:

1. safe known artifact classification/quarantine through `agents.lib.artifact_quarantine`
2. `agents.run_task._cleanup_runtime_artifacts_for_commit(...)` delegates through the extracted helper
3. warning/audit visibility is preserved after quarantine
4. unknown artifacts still block appropriately
5. quarantined artifacts do not silently disappear from decision output

## Exact forbidden patterns

- silently ignoring unknown artifacts
- weakening merge policy
- touching orchestrator engine files under `src/builder/orchestrator/`
- broad rewrites of `agents/run_task.py` outside the protected method scope above

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- known safe artifacts no longer require manual cleanup before PR
- `agents/run_task.py` is thinner after delegating artifact quarantine policy
