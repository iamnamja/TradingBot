# Task 062 — Orchestrator Integrated Capabilities E2E

## Goal

Deferred continuation task retained after the reliability/autonomy tranche.

Add a single realistic integrated end-to-end scenario that exercises multiple orchestrator capabilities added in tasks 043–054 together, while staying aligned to the **current live seams** and leaving dedicated failure-journal seam stabilization to Task 063.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_orchestrator_integrated_capabilities.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`

## Harness policy

- FILE: tests/test_orchestrator_integrated_capabilities.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_PRODUCT_SPEC.md MODE=DOCS_ONLY

## Required behavior

Add one integrated scenario that combines **at least three** of the following currently live capabilities in one realistic flow:

- frozen execution / spec-mode artifact resolution
- validator execution failure handling
- failure journal / failure reporting seam usage via the current live seam exports
- post-failure artifact bookkeeping that is already live in the repo
- task / seam preflight or localized bundle repair behavior that is already live in the repo

This task should **not** attempt to expand, redesign, or make stricter the current safe-parallelism review, runtime-quarantine behavior, or failure-journal seam family.

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

## Existing-seam guardrail

The integrated test added in this task must align with the **current live repository seams and behavior**. It must not invent new required APIs or strengthen optional surfaces into mandatory ones.

In particular:

- use the current failure-journal export shape exposed by `run_task._failure_journal_exports()`
- it is valid to reference the helper name `_failure_journal_exports`; do **not** invent alias names such as `failure_journal_export`
- do **not** require a new `"module"` key, a new `"report_failure"` export, or any new alias if the live seam does not expose one
- do **not** reference `_validator_runner_exports`, `validator_runner_exports`, `_shell_router_exports()`, `shell_router_export`, or any shell-router export helper from the generated test in this task
- preserve the current spec-mode frozen-task behavior exactly, including the current canonical task-text normalization used by the repo (`rstrip("\n")` behavior is acceptable if that is the live contract)
- the integrated test may assert only the currently live failure-journal export keys below and must not assert any additional keys:
  - `failure_journal`
  - `classify_failure`
  - `failure_fingerprint`
  - `bounded_failure_snippet`
  - `recommended_next_action`
  - `chosen_remediation_path`
  - `append_failure_journal_entry`
  - `retry_count_for_fingerprint`

## Required implementation shape

The generated test should be narrow and deterministic.

Preferred structure:

1. Import only the live helpers needed for the scenario:
   - `from agents import run_task`
   - `from agents.lib import check_runner, spec_mode, validator_runner`
2. Create a small temp task file and a temp frozen task file.
3. Resolve frozen/spec text through `spec_mode.resolve_task_text(...)`.
4. Monkeypatch `validator_runner._run_plugin_validators` to return a deterministic in-process validator failure.
5. Call `check_runner.run_checks(...)` directly to observe validator failure behavior.
6. Inspect `run_task._failure_journal_exports()` directly and assert exactly the live keyset listed above.
7. Stop after asserting the exact live `_failure_journal_exports()` keyset. Do not call exported failure-journal helper functions in this task.

The integrated test should look conceptually like this flow:

- resolve frozen text
- run a monkeypatched validator failure through `check_runner.run_checks(...)`
- assert failure result is observed
- assert `_failure_journal_exports()` keyset is exactly the live keyset
- assert `_failure_journal_exports()` keyset is exactly the live keyset and stop there

## Explicit prohibitions

Do **not** use any of these in the generated test:

- `run_task.main()`
- `run_task.run_task_shell(...)`
- `_shell_router_exports()`
- `shell_router_export`
- `run_task._failure_journal_exports()` is allowed and should not be treated as an invented alias
- `py -m agents.run_task`
- calling failure-journal export helpers such as `append_failure_journal_entry(...)` or `retry_count_for_fingerprint(...)` in this task
- direct subprocess recursion into repo-wide `pytest -q` or `ruff check .`

Do **not** assert or reference any non-live failure-journal export keys, including:

- `write_failure_journal`
- `build_failure_journal_entry`
- `load_failure_journal_entries`
- `build_failure_entry`

## Scope reduction guardrail

Do **not** modify or add these files in this task:

- `agents/run_task.py`
- `tests/test_execution_mode_frozen_task.py`
- `tests/test_failure_journal.py`
- `tests/test_safe_parallelism.py`
- `tests/test_runtime_artifact_quarantine.py`

Do not introduce new integrated assertions about:

- `run_review()` mergeability semantics
- non-empty `reasons` / `warnings` lists
- exact quarantine git-command sequences
- optional planner/review behavior
- failure-journal alias expansion or seam-family redesign
- direct validator export dictionaries or new validator export aliases
- shell-router helper/export aliases

## Nested-check guardrail

Integrated tests in this task must **not** trigger real nested repo-wide validator subprocesses from inside pytest.

In particular:

- do not call validator code in a way that shells out to real `ruff check .` or real `pytest -q` during the test run
- if validator behavior is part of the scenario, monkeypatch or fake the validator execution path so the test stays deterministic and in-process
- do not create tests that recursively invoke real repo-wide `pytest -q` from inside pytest
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
- the new integrated scenario uses at least three currently live capabilities together
- integrated tests do not weaken the existing focused unit tests
- no integrated test recursively invokes real repo-wide `pytest -q` or `ruff check .`
- the integrated tests align with current live seam names and current canonical task-text normalization
- this task does not modify `tests/test_execution_mode_frozen_task.py`, `tests/test_failure_journal.py`, `tests/test_safe_parallelism.py`, or `tests/test_runtime_artifact_quarantine.py`
- the product spec notes the existence and purpose of the integrated scenario coverage
- the product-spec update for this task lands in `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
