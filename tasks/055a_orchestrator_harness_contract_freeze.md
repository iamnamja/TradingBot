# Task 055a — Orchestrator Harness Contract Freeze

## Goal

Freeze the stable runner/shell contract so future reliability work stops accidentally regressing core surfaces while trying to add resilience.

## Execution lane

This task is **manual patch lane only**. Do not run it through the normal autonomous bundle lane.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_orchestrator_public_surface.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=request_and_parse_bundle TARGET_ANCHOR=def request_and_parse_bundle(
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=enforce_meta_file_task_gate TARGET_ANCHOR=def enforce_meta_file_task_gate(
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD TARGET_METHOD=_task_baseline_paths TARGET_ANCHOR=def enforce_meta_file_task_gate(
- FILE: agents/lib/shell_router.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=route_shell_main TARGET_ANCHOR=def route_shell_main(
- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

Freeze and regression-test the stable harness contract, including at least:

- module entrypoint / CLI reachability
- `request_and_parse_bundle(...)` compatibility surface
- `_normalize_policy_path(...)`
- `_task_baseline_paths(...)`
- `enforce_meta_file_task_gate(...)`
- shell-router compatibility with the live runner surface

## Compatibility guardrail

This task should **freeze** the contract, not broaden it. Prefer regression coverage over new capability.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py tests/test_orchestrator_public_surface.py` passes
- the stable harness surfaces are explicitly documented and protected by tests
