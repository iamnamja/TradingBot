# Task 042c — Extract Semantic Preflight

## Goal

Extract static contract enforcement and semantic preflight logic into a dedicated module, with no behavior change.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/lib/semantic_preflight.py`
- `agents/run_task.py`
- `tests/test_run_task_semantic_preflight_parity.py`

All listed files must be materially updated in the same bundle.

## Harness policy

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_module_source_for_name
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_module_exports_from_source
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_class_methods_from_source
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_class_init_arity_from_source
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=_protected_python_semantic_issues
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=validate_static_bundle_contracts
- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=_semantic_preflight_exports ANCHOR_BEFORE=if __name__ == "__main__":

## Critical compatibility requirement

This is a no-behavior-change extraction task.

The following behavior must remain intact:

- protected API import validation
- obvious constructor misuse detection
- forbidden import/call enforcement from machine-readable directives
- result-key contract enforcement
- current compatibility with monkeypatched helper shapes used by tests

## Required extraction targets

Move into `semantic_preflight.py`:

- static bundle contract validation
- protected Python semantic issue detection
- helper functions for module/source/export inspection used by semantic validation

`agents/run_task.py` must remain the public entrypoint, but the methods listed in the harness policy should become thin delegating wrappers over the extracted module.

Do NOT emit a normal full-file `FILE: agents/run_task.py` bundle for the protected file. Protected-file edits for `agents/run_task.py` must be satisfied only through the declared method replacement / append-method policy.

## Test requirements

Add deterministic parity tests for:

1. valid protected constructor usage
2. zero-arg constructor rejection
3. missing protected method call rejection
4. missing protected import symbol rejection
5. config-wrapper misuse rejection
6. non-protected code being ignored
7. compatibility with current monkeypatch styles used in semantic tests

## Exact forbidden patterns

- behavior changes to semantic policy
- weakening contract enforcement to get tests green
- touching orchestrator engine files under `src/builder/orchestrator/`
- broad rewrite of `agents/run_task.py`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` is fully green
- semantic preflight is modularized
- current behavior is preserved on the covered baseline
