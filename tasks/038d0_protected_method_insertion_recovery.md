# Task 038d0 — Protected Method Insertion Recovery

## Goal

Harden protected method insertion in `agents/run_task.py` so malformed-but-salvageable model responses do not fail the run before the requested method can be extracted.

## Why

Task 038d is currently blocked before validation/tests because the model sometimes returns malformed protected insertion output. The current harness retries once, but if parsing still fails it raises immediately.

This task should make protected insertion more fault-tolerant without weakening protected-file safety.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- FILE: agents/run_task.py MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=request_and_parse_method_insertion ANCHOR_BEFORE=validate_python_syntax( MAX_CHANGED_LINES=220
- `tests/test_run_task_method_insertion_recovery.py`

Both listed files must be materially updated in the same bundle.

## Scope

Keep the change narrowly focused on protected method-insertion parsing and recovery.

Do not change:
- provider/model selection behavior
- normal file-bundle parsing behavior
- protected-file policy enforcement
- append-method application rules
- workspace restore behavior
- virtual protected-file context behavior
- import validation behavior
- retry loop behavior outside protected insertion parsing/recovery

## Required implementation shape

For `agents/run_task.py`:

- Do not rewrite the full file.
- Use the protected append-method flow only.
- Add exactly one new top-level function named `request_and_parse_method_insertion`.
- Place it immediately before `def validate_python_syntax(`.
- The insertion payload must contain exactly one top-level function and nothing else.
- Do not add any additional top-level defs.
- Do not add any additional top-level classes.
- Do not add any additional top-level constants.
- Do not define nested helper functions inside `request_and_parse_method_insertion(...)`.
- Do not use any additional `def` statements anywhere inside the inserted method text.
- Keep helper logic inline using local variables, loops, comprehensions, `ast`, and existing stdlib calls only.
- For the protected insertion response, return only the method insertion payload requested by the harness. Do not emit a normal `BEGIN_FILE_BUNDLE` response for `agents/run_task.py`.

### Required method signature

```python
def request_and_parse_method_insertion(messages: List[dict], model: str, provider: str, last_output_path: Path, expected_path: str, expected_method_name: str) -> str:
```

The inserted `request_and_parse_method_insertion(...)` method must remain backward compatible and preserve the current successful parsing paths.

## Required behavior

Improve the protected method-insertion flow so it can recover when the model returns malformed content that still clearly includes the requested method body.

At minimum, support these cases for protected insertion responses:

1. valid `BEGIN_METHOD_INSERTION` / `END_METHOD_INSERTION` payload
2. valid normal `BEGIN_FILE_BUNDLE` payload containing the protected target file
3. malformed normal file bundle where the raw text still contains exactly one recoverable top-level `def <expected_method_name>(...)` block

### Safety rules

Recovery must still fail if:
- zero matching method definitions are found
- more than one matching method definition is found
- the extracted method name does not exactly match the expected method
- the recovered method body cannot be parsed as Python syntax
- the recovered method would violate the existing single-method insertion rule

### Recovery behavior

- Keep the existing success paths intact.
- After the normal retry fails, perform a raw-text recovery pass before raising `FileBundleError`.
- Recovery should only extract the expected method and should not accept arbitrary surrounding bundle text as valid.
- Use Python syntax parsing to validate the recovered method text.
- Preserve current error messages where possible, but include the recovery failure reason when recovery is attempted and fails.

## Exact forbidden patterns

- rewriting all of `agents/run_task.py`
- emitting multiple top-level methods in the protected insertion payload
- using nested helper defs inside `request_and_parse_method_insertion`
- adding helper methods at top level
- adding extra `def` statements anywhere in the inserted payload
- changing provider/model defaults
- changing protected-file baseline logic
- changing append-method parsing behavior outside the targeted recovery behavior
- touching orchestrator production files
- touching TradingBot production files
- relying on external services in tests

## Tests

`tests/test_run_task_method_insertion_recovery.py` must cover at least:

1. standard method insertion bundle parses
2. normal full file bundle parses and extracts the expected method
3. malformed file bundle with one recoverable expected method is accepted
4. malformed response with multiple matching expected methods fails
5. malformed response with wrong method name fails
6. malformed response with invalid Python method syntax fails

Tests must be deterministic, Windows-portable, and self-contained.

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- protected insertion can recover from malformed-but-salvageable model output
- `agents/run_task.py` changes are limited to one additive protected-method insertion
