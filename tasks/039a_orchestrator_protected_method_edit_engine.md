# Task 039a — Protected Method Edit Engine (Tests Only)

## Goal

Add deterministic tests for the current protected method edit engine behavior in `agents/run_task.py` without changing production code.

## Why

We are pausing production changes to the harness so we can validate the current protected method edit engine before continuing the hardening tranche.

This task must verify the existing append-method and replace-method behavior already present in `agents/run_task.py`.

## Deliverables

Create or update these exact files. Every listed file must appear in the bundle:

- `tests/test_run_task_protected_method_edit_engine.py`

The listed file must be materially updated.

## Harness policy

- FILE: agents/run_task.py MODE=PROTECTED_FORBID

## Critical compatibility requirement

This task adds tests only.

It must not change:
- `agents/run_task.py`
- provider/model selection behavior
- bundle parsing behavior
- git / branch behavior
- any file under `src/`

All existing passing tests must continue to pass.

## Current baseline under test — use exact current behavior

Only import symbols that actually exist on the current baseline.

The tests must target these real functions with their real current signatures and current behavior:

- `parse_harness_file_policies(task_text)`
  - returns a dict keyed by file path
  - each value is a dict containing a `"rules"` list
  - rules are normalized to internal policy strings such as:
    - `forbid`
    - `exact_copy`
    - `append_before:<anchor>`
    - `allow_methods:<name>`
    - `replace_method:<name>`
    - `max_changed_lines:<n>`

- `_extract_protected_method_targets(task_text)`
  - returns a list of dict objects, not tuples
  - use keys such as:
    - `"path"`
    - `"mode"` (`"append"` or `"replace"`)
    - `"method_name"`
    - `"anchor"` for append targets
    - optional `"max_changed_lines"`
  - do NOT expect keys like:
    - `"kind"`
    - `"rules"`
    - `"target_method"`

- `apply_method_insertion(original, anchor, method_name, method_text)`
  - returns the updated file content as a string
  - raises `run_task.FileBundleError` on invalid input
  - the inserted method is re-indented to match its insertion context

- `apply_method_replacement(original, method_name, method_text)`
  - returns the updated file content as a string
  - raises `run_task.FileBundleError` on invalid input

- `parse_method_insertion_bundle(text, expected_path, expected_method_name)`
  - returns the extracted method text as a string on success
  - raises `run_task.FileBundleError` on malformed bundle structure or wrong expected method name

- `request_and_parse_method_insertion(messages, model, provider, last_output_path, expected_path, expected_method_name)`
  - returns the extracted method text as a string on success
  - calls `chat(messages, model=model, provider=provider)` without an `output_path` parameter
  - `last_output_path` must be a real `pathlib.Path`
  - for this function, monkeypatch `agents.run_task.chat`
  - do NOT call the real external model

## Required test scenarios

Add deterministic tests covering at least:

1. append policy parsing from a realistic task snippet using:
   - a `## Harness policy` section
   - `- FILE: ... MODE=EXACT_COPY_PLUS_APPEND_METHOD ALLOW_NEW_METHOD=... ANCHOR_BEFORE=...`
   - use an anchor token with no spaces, such as `_parse_task_file(` or `existing(`
   - assert normalized rules like:
     - `append_before:def _parse_task_file(`
     - `allow_methods:simulate_backlog`

2. replace policy parsing from a realistic task snippet using:
   - a `## Harness policy` section
   - `- FILE: ... MODE=EXACT_COPY_PLUS_REPLACE_METHOD TARGET_METHOD=...`
   - assert normalized rules include:
     - `replace_method:<name>`
   - it is acceptable if the current baseline also includes:
     - `allow_methods:<name>`

3. append target extraction from a realistic task snippet using:
   - `ANCHOR_BEFORE=...`
   - `ALLOW_NEW_METHOD=...`
   - assert exact core fields on the returned dict:
     - `target["path"] == "agents/example.py"`
     - `target["mode"] == "append"`
     - `target["method_name"] == "simulate_backlog"`
     - `target["anchor"] == "def _parse_task_file("`
   - do NOT inspect `target["rules"]`
   - do NOT expect `target["kind"]`

4. replace target extraction from a realistic task snippet using:
   - `TARGET_METHOD=...`
   - assert exact core fields on the returned dict:
     - `target["path"] == "agents/example.py"`
     - `target["mode"] == "replace"`
     - `target["method_name"] == "validate_static_bundle_contracts"`
   - it is acceptable for the dict to also include:
     - `"max_changed_lines": None`
   - do NOT expect `target["target_method"]`
   - do NOT inspect `target["rules"]`

5. append method application into baseline content before an anchor
   - assert:
     - the helper method appears before the anchor method
     - the helper definition is present
     - the helper body line is present
     - the helper is indented according to the surrounding context
   - do NOT assert one exact flat string like `def helper(self):\n    return 3\n`

6. replace method application for an existing method
   - do not require an exact full-string match
   - assert instead that:
     - the new exact body line is present
     - the old exact body line is gone
     - surrounding methods remain present
   - avoid substring overlaps like asserting `"return 2"` is absent when `"return 200"` is present

7. missing replacement target rejection

8. missing append anchor rejection

9. malformed bundle rejection for `parse_method_insertion_bundle(...)`
   - use a structurally malformed bundle, for example a bundle that is missing `END_FILE`
   - use `pytest.raises(run_task.FileBundleError)`
   - do NOT use a structurally valid bundle whose only issue is that the function body is incomplete

10. `request_and_parse_method_insertion(...)` happy-path parsing using monkeypatched `chat`
    - monkeypatched `chat` must accept exactly `(messages, model, provider)`
    - pass a real `pathlib.Path` as `last_output_path`
    - the synthetic bundle must contain a valid extracted method body with proper indentation, for example:
      - `def helper(self):`
      - `    return 3`
    - assert the function returns the extracted method text string exactly:
      - `def helper(self):\n    return 3\n`

11. `request_and_parse_method_insertion(...)` malformed bundle rejection using monkeypatched `chat`
    - use a structurally malformed bundle or a bundle containing the wrong method name
    - use `pytest.raises(run_task.FileBundleError)`

## Strong guidance — use these fixture shapes

Use helper functions in the test file so the shapes stay exact.

### Example harness-policy fixture

Use a helper like:

```python
def _policy_text(*lines: str) -> str:
    return "\n".join(["# Task title", "", "## Harness policy", "", *lines]).strip()
```

For append policy tests, use this exact shape:

```python
task_text = _policy_text(
    "- FILE: agents/example.py MODE=EXACT_COPY_PLUS_APPEND_METHOD "
    "ALLOW_NEW_METHOD=simulate_backlog ANCHOR_BEFORE=_parse_task_file("
)
```

Expected normalized rules should include:

```python
rules = policies["agents/example.py"]["rules"]
assert "append_before:def _parse_task_file(" in rules
assert "allow_methods:simulate_backlog" in rules
```

For replace policy tests, use this exact shape:

```python
task_text = _policy_text(
    "- FILE: agents/example.py MODE=EXACT_COPY_PLUS_REPLACE_METHOD "
    "TARGET_METHOD=validate_static_bundle_contracts"
)
```

Expected normalized rules should include:

```python
rules = policies["agents/example.py"]["rules"]
assert "replace_method:validate_static_bundle_contracts" in rules
```

It is acceptable if `allow_methods:validate_static_bundle_contracts` is also present.

### Example append insertion fixture

Use a class-method context so indentation is explicit:

```python
original = "\n".join(
    [
        "class Example:",
        "    def existing(self):",
        "        return 1",
        "",
    ]
) + "\n"

method_text = "\n".join(
    [
        "def helper(self):",
        "    return 3",
        "",
    ]
)
```

Then assert all of:
- `"    def helper(self):"` is in the updated string
- `"        return 3"` is in the updated string
- `"def helper(self):"` appears before `"def existing(self):"`

### Example happy-path request/parse fixture

The monkeypatched `chat` must accept exactly:

```python
def fake_chat(messages, model, provider):
    ...
```

The synthetic bundle text should be built indirectly and should contain a valid method block, for example:

```python
bundle = "\n".join(
    [
        "BEGIN_" + "FILE_BUNDLE",
        "FI" + "LE: agents/run_task.py",
        "def helper(self):",
        "    return 3",
        "END_" + "FILE",
        "END_" + "FILE_BUNDLE",
        "",
    ]
)
```

Expected success assertion:

```python
assert result == "def helper(self):\n    return 3\n"
```

### Example malformed parse fixture

Use a structurally malformed bundle, for example:

```python
malformed = "\n".join(
    [
        "BEGIN_" + "FILE_BUNDLE",
        "FI" + "LE: agents/run_task.py",
        "def helper(self):",
        "    return 3",
        "END_" + "FILE_BUNDLE",
        "",
    ]
)
```

This should raise `run_task.FileBundleError` because `END_FILE` is missing.

## Test construction rules

- Use normal imports from `agents.run_task`
- Do not mock the entire module
- For payload tests, use synthetic baseline strings and synthetic bundle text
- Keep tests Windows-portable and self-contained
- Do not call external services
- Do not modify repo files during the tests

### CRITICAL: use real task section layout for extraction tests

`parse_harness_file_policies(...)` only parses `- FILE:` directives from supported sections such as `## Harness policy`.

So the extraction tests must place their `- FILE:` lines under a real `## Harness policy` heading.

### CRITICAL: use real policy attribute names

For append extraction tests, use `ANCHOR_BEFORE=...`, not `ANCHOR=...`.

Also, because the current parser tokenizes attribute values on spaces, do not use anchors with spaces such as:
- `class Example:`

Use anchors without spaces, such as:
- `_parse_task_file(`
- `existing(`

### CRITICAL: use the real exception/return contracts

Do NOT assert invented wrapper dicts like:
- `{"ok": True, ...}`
- `{"ok": False, "error": ...}`

For these functions, use the current real behavior:
- successful functions return plain strings
- invalid input raises `run_task.FileBundleError`

### CRITICAL: avoid overspecifying exact whitespace or substring overlaps

For `apply_method_replacement(...)`, do not use brittle checks like asserting `"    return 2"` is absent when the replacement body contains `"    return 200"`.

Prefer assertions that check:
- the exact old method body line, such as `"return 2\n"`, is gone
- the new exact body line, such as `"return 200\n"`, is present
- untouched methods remain present

For `apply_method_insertion(...)`, prefer assertions that check:
- helper method appears before anchor
- helper definition is present
- helper body line is present with surrounding-context indentation

### CRITICAL bundle-string construction rule

Because the outer agent harness parses `FILE:` / `END_FILE` markers literally, the generated test file must NOT contain a triple-quoted source fixture with literal lines that begin with:

- `FILE:`
- `END_FILE`
- `BEGIN_FILE_BUNDLE`
- `END_FILE_BUNDLE`

inside the emitted file contents.

Instead, when constructing synthetic bundle text inside the test file, build those markers indirectly, for example:
- with `"FI" "LE:"` string splitting
- or with `"BEGIN_" + "FILE_BUNDLE"`
- or with `"\n".join([...])`

so the final runtime string is correct, but the emitted source file does not contain literal bundle-marker lines that confuse the outer parser.

## Exact forbidden patterns

- modifying `agents/run_task.py`
- creating `tests/test_run_task_protected_api_semantic_preflight.py`
- replacing or focusing on `validate_static_bundle_contracts(...)`
- solving semantic/API preflight instead of protected method edit engine
- modifying any file under `src/`
- using triple-quoted fixtures that contain literal line-start bundle markers like `FILE:` or `END_FILE`
- asserting tuple results for `_extract_protected_method_targets(...)`
- calling `apply_method_insertion(...)`, `apply_method_replacement(...)`, `parse_method_insertion_bundle(...)`, or `request_and_parse_method_insertion(...)` with invented signatures
- asserting dict return values from `parse_method_insertion_bundle(...)` or `request_and_parse_method_insertion(...)`
- using `## Task` instead of `## Harness policy` for `- FILE:` extraction fixtures
- using `ANCHOR=` in append extraction tests
- monkeypatching `chat` with an `output_path` parameter
- using append anchors that contain spaces, such as `class Example:`
- expecting target dict keys like `kind`, `rules`, or `target_method`

## Acceptance criteria

- `ruff check .` passes
- `pytest -q` passes
- the current protected method edit engine is covered by deterministic tests without production edits
