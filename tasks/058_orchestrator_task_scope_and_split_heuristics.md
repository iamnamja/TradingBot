# Task 058 — Orchestrator Task Scope / Split Heuristics

## Goal

Teach the orchestrator to recognize when a task likely spans multiple seam families and should be split, instead of forcing too-broad tasks through many iterations.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`

## Harness policy

- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_VISION_AND_CONTROLS.md MODE=DOCS_ONLY

## Required behavior

Add lightweight task-scope heuristics that can detect likely over-broad tasks, especially when they mix multiple seam families such as:

- bootstrap/config surfaces
- failure-journal/reporting seams
- safe-parallelism/review semantics
- runtime artifact quarantine behavior
- broad docs normalization

The heuristic should be able to advise that a task be split into focused follow-ons rather than forcing all scope through one request.

## Compatibility constraints

- this task is about guidance and guardrails, not mandatory auto-splitting of every task
- the harness may warn, annotate, or recommend subtasks
- avoid introducing brittle or overly opinionated logic

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the harness can identify at least one broad multi-seam task shape and recommend splitting
- docs explain the heuristic intent and when a split recommendation appears
