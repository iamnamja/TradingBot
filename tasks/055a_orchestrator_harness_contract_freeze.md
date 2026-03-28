# Task 055a — Orchestrator Harness Contract Freeze

## Goal

Freeze the stable runner/shell contract so future reliability work stops accidentally regressing core surfaces while trying to add resilience.

## Execution lane

This task is a **manual patch lane bootstrap task**.

Do **not** run it through the normal autonomous generation lane. Implement it directly and merge it first. The purpose of this task is to stabilize the engine contract that later autonomous tasks depend on.

## Deliverables

Create or update these exact files:

- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_orchestrator_public_surface.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

Freeze and regression-test the stable harness contract, including at least:

- module entrypoint / CLI reachability (covered by the live runner contract)
- `request_and_parse_bundle(...)` compatibility surface
- `_normalize_policy_path(...)`
- `_task_baseline_paths(...)`
- `enforce_meta_file_task_gate(...)`
- shell-router compatibility with the live runner surface, including:
  - baseline loading through `_task_baseline_paths(...)`
  - compatibility with both older and newer `request_and_parse_bundle(...)` call shapes

## Compatibility guardrail

This task should **freeze** the contract, not broaden it. Prefer regression coverage over new capability.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q tests/test_run_task_runtime_foundations.py tests/test_orchestrator_public_surface.py` passes
- the stable harness surfaces are explicitly documented and protected by tests
