# Task 039a — Protected Method Edit Engine

## Goal

Unify protected method editing in `agents/run_task.py` so append-method and replace-method tasks both work reliably with one consistent target extractor, prompt builder, parser, recovery path, and apply path.

## Why

Protected Python files are the highest-risk part of the orchestrator backlog. The harness already has append-style protected method insertion, but the current flow is still fragmented and brittle when tasks need method replacement rather than append-only edits.

This task comes first because later harness hardening tasks depend on a reliable protected-file edit engine.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `agents/run_task.py`
- `tests/test_run_task_protected_method_edit_engine.py`

Both listed files must be materially updated.

## Scope

Keep the change narrowly focused on protected method edit handling in the harness.

Do not change:
- provider/model selection behavior
- normal bundle parsing behavior
- git / branch behavior
- TradingBot or orchestrator production code under `src/`
- semantic/API preflight behavior in `validate_static_bundle_contracts(...)`

## Required protected modes

The harness must support both append-method mode and replace-method mode.

### Append-method mode

Support task specs that declare all of the following:
- a protected Python file path
- `MODE=EXACT_COPY_PLUS_APPEND_METHOD`
- an append anchor such as `ANCHOR_BEFORE=some_anchor(`
- the allowed new method name such as `ALLOW_NEW_METHOD=new_method`

### Replace-method mode

Support task specs that declare all of the following:
- a protected Python file path
- `MODE=EXACT_COPY_PLUS_REPLACE_METHOD`
- a replacement target such as `TARGET_METHOD=existing_method`

Important:
- The examples in this section are descriptive only.
- Do not treat this section as literal file directives.
- The only real file changes for this task are the deliverables listed above.

## Required behavior

Add a unified protected method target extractor and edit engine that:

1. parses append and replace targets from task text
2. builds the correct model prompt for each mode
3. parses the protected method payload robustly
4. applies the method edit safely to the protected baseline
5. rejects payloads that define zero or multiple methods
6. keeps the exact-copy discipline outside the targeted method edit

### Recovery behavior

Retain the current malformed-output retry behavior, but the same recovery path must work for both append and replace modes.

### Failure messaging

Examples of expected errors:

- `Protected method replacement target 'validate_imports' was not found in agents/run_task.py`
- `Method insertion payload must define exactly one method 'validate_imports'`
- `Protected append target requires anchor 'missing_module_hints(' but it was not found`

## CRITICAL task identity

This task is about the protected method edit engine only.

It is NOT the semantic preflight task.

The bundle for this task must:
- update `agents/run_task.py`
- create/update `tests/test_run_task_protected_method_edit_engine.py`

The bundle for this task must NOT:
- create `tests/test_run_task_protected_api_semantic_preflight.py`
- replace or focus on `validate_static_bundle_contracts(...)`
- add semantic constructor/import/method-call validation logic
- solve Task 039b instead of Task 039a

## Exact forbidden patterns

- solving semantic/API preflight instead of protected method edit engine
- creating `tests/test_run_task_protected_api_semantic_preflight.py`
- replacing `validate_static_bundle_contracts(...)`
- adding tests for `OrchestratorRunner()` constructor misuse in this task
- adding tests for missing protected imports in this task
- modifying any file under `src/`

## Tests

`tests/test_run_task_protected_method_edit_engine.py` must include deterministic tests for at least:

1. append target extraction
2. replace target extraction
3. append method application
4. replace method application
5. duplicate-method payload rejection
6. missing-target / missing-anchor rejection
7. malformed protected payload retry/recovery for both modes

Tests must be Windows-portable and must not call external services.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- protected method edits are handled by one unified engine for append and replace use cases
