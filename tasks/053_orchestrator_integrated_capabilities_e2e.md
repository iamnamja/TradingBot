# Task 053 — Orchestrator Integrated Capability Scenarios

## Goal

Add integrated end-to-end scenarios that exercise the capabilities added in tasks 043–048 together instead of only in isolation.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_integrated_capabilities.py`
- `tests/test_safe_parallelism.py`
- `tests/test_failure_journal.py`
- `tests/test_execution_mode_frozen_task.py`
- `tests/test_runtime_artifact_quarantine.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_integrated_capabilities.py MODE=TESTS_ONLY
- FILE: tests/test_safe_parallelism.py MODE=TESTS_ONLY
- FILE: tests/test_failure_journal.py MODE=TESTS_ONLY
- FILE: tests/test_execution_mode_frozen_task.py MODE=TESTS_ONLY
- FILE: tests/test_runtime_artifact_quarantine.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

Add realistic integrated scenarios covering combinations such as:

- runtime artifact quarantine + failure journal
- spec mode + frozen execution + validator selection
- bootstrap/project adapter + validator plugins
- safe parallelism gating + protected-file restrictions

## Critical compatibility constraint

This task is additive integrated-test coverage work.

Do not use this task to redesign or relocate the post-050/052 public/bootstrap/config surfaces.

In particular, the following existing helpers and import locations must remain intact after this task:

- `builder.orchestrator.project_config.load_project_config`
- `builder.orchestrator.project_config.bootstrap_project_config_scaffold`
- `builder.orchestrator.project_adapter.load_project_adapter`
- `builder.orchestrator.project_adapter.bootstrap_project_adapter_scaffold`
- `builder.orchestrator.project_adapter.build_bootstrap_starter_docs_text`
- `builder.orchestrator.project_adapter.build_bootstrap_task_template_text`

## Test-shape guidance

Prefer composing the existing focused helpers/fixtures rather than re-implementing large bespoke setups.

These integrated tests should **layer on top of** the existing focused unit tests, not replace or weaken them.

At least one scenario should exercise **three or more** of the 043–048 capabilities in one realistic flow.

Do not modify non-listed code files in this task.

## Nested-check guardrail

Integrated tests in this task must **not** trigger real nested repo-wide validator subprocesses from inside pytest.

In particular:

- do not call `validator_runner.run_checks(...)` in a way that shells out to real `ruff check .` or real `pytest -q` during the test run
- if validator behavior is part of the scenario, monkeypatch or fake the validator execution path so the test stays deterministic and in-process
- do not create tests that recursively invoke repo-wide `pytest -q` from inside pytest
- keep integrated scenarios fast, deterministic, and bounded

It is acceptable to monkeypatch:
- `agents.lib.validator_runner._run_plugin_validators`
- `agents.lib.check_runner.run_checks`
- `subprocess.run`

so long as the scenario still proves the intended orchestration wiring and compatibility behavior.

## Docs-path constraint

Use `docs/` as the canonical location for orchestrator narrative docs.

Do not create or modify a root-level `ORCHESTRATOR_PRODUCT_SPEC.md` in this task.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least one new integrated scenario uses 3 or more of the 043–048 capabilities together
- integrated tests do not weaken the existing focused unit tests
- no integrated test recursively invokes real repo-wide `pytest -q` or `ruff check .`
- the product spec notes the existence and purpose of the integrated scenario coverage
- the product-spec update for this task lands in `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
