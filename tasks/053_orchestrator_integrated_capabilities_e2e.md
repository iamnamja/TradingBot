# Task 053 — Orchestrator Integrated Capability Flow

## Goal

Add **one** realistic integrated end-to-end scenario that proves multiple orchestrator capabilities from tasks 043–048 work together, without tightening optional or loosely-defined seams that are better handled in follow-on tasks.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_integrated_capabilities.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_integrated_capabilities.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

Add exactly one integrated scenario that combines **at least three** currently live capabilities in one flow, using only seams already stable in the repo.

Recommended combination:
- frozen execution / canonical frozen task text resolution
- in-process validator failure handling (monkeypatched, no nested subprocess validators)
- failure output / failure-journal seam alignment at the current live contract

## Critical compatibility constraint

This task is additive integrated coverage work.

Do not redesign or relocate the post-050/052 public/bootstrap/config surfaces.

In particular, these existing helpers and import locations must remain intact:

- `builder.orchestrator.project_config.load_project_config`
- `builder.orchestrator.project_config.bootstrap_project_config_scaffold`
- `builder.orchestrator.project_adapter.load_project_adapter`
- `builder.orchestrator.project_adapter.bootstrap_project_adapter_scaffold`
- `builder.orchestrator.project_adapter.build_bootstrap_starter_docs_text`
- `builder.orchestrator.project_adapter.build_bootstrap_task_template_text`

## Existing-seam guardrail

The integrated scenario must align with the **current live repository seams and behavior**.

In particular:

- use the current failure-journal export shape exposed by `run_task._failure_journal_exports()`
- do **not** require a new `"module"` key, a new `"report_failure"` export, or any new alias if the live seam does not expose one
- preserve the current spec-mode frozen-task behavior exactly, including current canonical task-text normalization (current `rstrip("\n")` behavior is acceptable if that is the live contract)
- the scenario may assert:
  - return code `1` for the simulated failing flow **only if** the in-process mock path actually fails
  - failure output contains the current live max-iteration or validator-failure message
  - canonical task text was resolved from the frozen artifact
  - validator failure was observed through the in-process seam under test
- the scenario must **not** require direct observation of a failure-report seam unless the live routed path actually calls the patched seam

## Scope exclusions

Do **not** modify or add these files in this task:

- `tests/test_execution_mode_frozen_task.py`
- `tests/test_failure_journal.py`
- `tests/test_safe_parallelism.py`
- `tests/test_runtime_artifact_quarantine.py`

Those are handled by follow-on tasks.

Do not introduce integrated assertions about:
- safe-parallelism planner optionality
- protected-file review mergeability semantics
- non-empty `reasons` / `warnings` lists
- exact quarantine git-command sequences

## Nested-check guardrail

This integrated test must **not** trigger real nested repo-wide validator subprocesses from inside pytest.

In particular:

- do not call `validator_runner.run_checks(...)` in a way that shells out to real `ruff check .` or real `pytest -q`
- monkeypatch or fake validator execution so the test stays deterministic and in-process
- do not recursively invoke repo-wide `pytest -q` from inside pytest

## Docs-path constraint

Use `docs/` as the canonical location for orchestrator narrative docs.

Do not create or modify a root-level `ORCHESTRATOR_PRODUCT_SPEC.md` in this task.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the new integrated scenario uses at least three currently live capabilities together
- integrated coverage remains aligned with the current live seam contracts
- no nested repo-wide validator subprocesses are invoked
- the product spec notes the existence and purpose of this integrated-flow coverage in `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
