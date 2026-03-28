# Task 055b — Orchestrator Task Family Classifier, Prompt Compiler, and Split Strategy

## Goal

Teach the orchestrator to recognize task families, compile the right lane-specific request for each family, and warn when a task is broad enough that it should be split.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/task_contracts.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=build_messages TARGET_ANCHOR=def build_messages(
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY

## Required behavior

Add lightweight task-family classification for at least:

- docs-only
- narrow tests-only
- integration-test
- protected meta-harness

The classifier should influence prompting/strategy selection and should be able to emit a split recommendation when a task mixes multiple risky seam families.

The prompt compiler should be able to produce a **different request shape per lane** instead of one generic prompt for all task families.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py` passes
- the runner can identify at least one multi-seam task shape and recommend a split
- docs explain task families, lane-specific prompt compilation, and why they matter
