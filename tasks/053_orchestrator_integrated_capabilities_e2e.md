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
- `ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_integrated_capabilities.py MODE=TESTS_ONLY
- FILE: tests/test_safe_parallelism.py MODE=TESTS_ONLY
- FILE: tests/test_failure_journal.py MODE=TESTS_ONLY
- FILE: tests/test_execution_mode_frozen_task.py MODE=TESTS_ONLY
- FILE: tests/test_runtime_artifact_quarantine.py MODE=TESTS_ONLY
- FILE: ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

Add realistic integrated scenarios covering combinations such as:

- runtime artifact quarantine + failure journal
- spec mode + frozen execution + validator selection
- bootstrap/project adapter + validator plugins
- safe parallelism gating + protected-file restrictions

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- at least one new integrated scenario uses 3 or more of the 043–048 capabilities together
- integrated tests do not weaken the existing focused unit tests
