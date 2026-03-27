# Task 054 — Orchestrator Task / Seam Preflight Linter

## Goal

Add a lightweight, seam-aware preflight that catches common task-generation mistakes **before** a full iteration consumes a candidate bundle, with emphasis on live seam-name validation, recursive-validator protection, canonical docs-path discipline, task-scope drift, and obviously unsafe candidate rewrites.

This task is intended to make the harness **more resilient to bad generated bundles** without turning it into a full static analyzer or redesigning the current shell/runtime architecture.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_orchestrator_public_surface.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

Do **not** modify any other files in this task.

## Harness policy

- FILE: tests/test_run_task_runtime_foundations.py MODE=TESTS_ONLY
- FILE: tests/test_orchestrator_public_surface.py MODE=TESTS_ONLY
- FILE: docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md MODE=DOCS_ONLY

## Required behavior

Add a shallow preflight step that runs on the parsed/generated candidate bundle before normal write/check execution continues.

The preflight may inspect:

- the task text
- the parsed bundle contents
- the live repository files already on disk
- the current live shell seam registry / export helpers

The preflight must catch, block, or explicitly report at least these mistake classes:

1. **Nonexistent seam names / monkeypatch targets**
   - detect references to seam names or monkeypatch targets that do not exist in the live repository contract
   - use the current live seam/export surfaces as the source of truth rather than invented aliases

2. **Recursive repo-wide validator invocation from tests**
   - detect integrated tests that appear to invoke real repo-wide `pytest -q` or `ruff check .`
   - this protection is specifically for accidental nested validation recursion, not for normal in-process unit tests

3. **Canonical docs path drift**
   - `README.md` is canonical at the repository root
   - orchestrator / tradingbot narrative docs are canonical under `docs/`
   - obvious moved/renamed canonical-doc drift should be reported before execution

4. **Task/deliverable scope drift**
   - generated files outside the task's listed deliverables should be flagged
   - the check should be deterministic and based on the task's explicit deliverables rather than broad heuristics

5. **Suspicious miniature rewrite / stub collapse for existing harness files**
   - add at least one conservative guard against replacing an existing nontrivial harness file with an obviously simplified stub or toy implementation
   - this guard should be narrow and low-noise; it is acceptable to apply it only to the files touched by this task family, especially `agents/run_task.py`

6. **Obvious Python text corruption indicators**
   - catch clearly suspicious Python-source text issues before full execution when practical
   - examples include typographic quote characters accidentally emitted into code-like contexts, or similarly obvious bundle-generation artifacts that are very likely to produce syntax failures

## Localized-repair behavior

When the harness can localize a preflight or syntax problem to a subset of generated files, it should prefer a **targeted repair / retry** for the offending files instead of needlessly discarding and regenerating the entire bundle.

This should remain lightweight. Do **not** implement a general-purpose multi-stage compiler or static-analysis framework.

A practical implementation is acceptable so long as:

- accepted files can remain untouched when only one or two files are bad
- the retry/request text is explicit about which files need correction and why
- the overall iteration remains deterministic and bounded

## Critical compatibility guardrails

This task must be **additive and safe**.

Do **not** use this task to redesign, relocate, or simplify away the existing runner/shell architecture.

In particular:

- preserve the current CLI entrypoint and main run loop behavior
- preserve current shell-routing structure and public export families
- preserve current live seam names rather than inventing friendlier aliases
- do not replace large existing modules with minimal placeholders or toy stubs
- do not broaden this task into a full repository linter or full static analyzer

The current live compatibility surface should remain intact after this task. In particular, existing helpers such as the following must remain present unless a strictly additive refactor preserves them fully:

- `main`
- `build_messages`
- `request_and_parse_bundle`
- `run_checks`
- `validate_python_syntax`
- `_shell_router_exports()`
- `_failure_journal_exports()`

This task should **not** change the live shell-router public contract merely to make tests easier.

## Existing-live-contract guardrail

Tests and implementation added in this task must align with the **current live repository contract**.

In particular:

- use the live seam registry / export helpers as the source of truth
- do **not** rename the current failure-journal seam from `_report_failure` to `report_failure`
- do **not** introduce new mandatory seam aliases that the current repo does not expose
- do **not** assert new shell export shapes unless they are actually added in a backward-compatible way

## Scope discipline guardrail

Do **not** use this task to:

- rewrite `agents/run_task.py` wholesale
- move docs between root and `docs/` beyond the documented canonical-path checks
- redesign safe-parallelism, runtime-quarantine, bootstrap, spec-mode, or failure-journal behavior
- add new integrated end-to-end scenarios unrelated to preflight

Keep the changes surgical and centered on **preflight detection/reporting plus localized repair behavior**.

## Reporting behavior

If a preflight issue is advisory rather than blocking, that must be explicit in the message.

Issue messages should be:

- short
- deterministic
- actionable
- specific about the file, seam, or deliverable that triggered the issue

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- the harness can catch at least the listed mistake classes before consuming a full iteration
- the runner preserves the current live seam/export contract while adding the new preflight behavior
- localized retry/repair is used when only a subset of generated files is invalid or obviously corrupted
- controls/policies docs explain what the preflight checks, what is blocking vs advisory, and how localized repair is reported
