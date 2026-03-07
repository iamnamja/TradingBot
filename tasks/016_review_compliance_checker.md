# Task 016: Review/compliance checker

## Goal
Build a review/compliance checker that can inspect a task result and decide whether it is safe to merge.

## Deliverables
- `src/builder/orchestrator/review.py`
  - `class ReviewChecker`
  - method(s) to evaluate:
    - deliverable compliance
    - out-of-scope file changes
    - runtime artifact presence

- `tests/test_review_checker.py`

## Required behavior

### Inputs
The checker should accept enough information to review a task result, such as:
- task deliverables
- changed files
- optional test/lint result summary

### Semantics
For this task, `deliverables` means the files that are **in scope / allowed to change** for the task.

It does **not** mean that every deliverable must have changed.

This is the most important rule in the task.

### Required checks
The checker must detect:
- whether at least one changed file is within the allowed deliverables set
- unexpected extra changed files
- likely runtime artifacts such as:
  - files under `logs/`
  - generated cache/temp files

### Mergeable rule
A result is mergeable if:
- at least one changed file is within the allowed deliverables set
- there are no unexpected non-artifact changed files

### Runtime artifacts
Artifact-path matches such as `logs/...`, `*.tmp`, or `*.cache` should:
- appear in `warnings`
- not block mergeability by themselves
- be ignored for scope-compliance purposes

### Missing deliverables
Only report `Missing deliverables: ...` if **none** of the changed files are within the allowed deliverables set.

Do **not** report missing deliverables merely because some in-scope deliverables did not change.

This message must list filenames in sorted alphabetical order.

### Unexpected changes
If changed files include non-artifact files outside the deliverables set, report:
- `Unexpected changes: ...`

This message must list filenames in sorted alphabetical order.

### Warnings ordering
When reporting runtime artifacts in `warnings`:
- preserve the order in which the artifact files appear in `changed_files`
- do **not** sort warnings alphabetically

### Verdict
Return a structured verdict that includes:
- `mergeable: bool`
- `reasons: list[str]`
- `warnings: list[str]`

### Deterministic output
- sort filenames alphabetically in `reasons`
- preserve `changed_files` order for `warnings`

## Normative examples

### Example 1: valid scoped change
- `deliverables = ["file1.py", "file2.py"]`
- `changed_files = ["file1.py"]`
- `mergeable = True`
- `reasons = []`

### Example 2: missing deliverables + unexpected change
- `deliverables = ["file1.py", "file2.py"]`
- `changed_files = ["file3.py"]`
- `mergeable = False`
- `reasons` include:
  - `Missing deliverables: file1.py, file2.py`
  - `Unexpected changes: file3.py`

### Example 3: runtime artifact warning only
- `deliverables = ["file1.py"]`
- `changed_files = ["file1.py", "logs/error.log"]`
- `mergeable = True`
- `warnings` include:
  - `Detected runtime artifact: logs/error.log`

### Example 4: multiple warnings preserve input order
- `deliverables = ["file1.py"]`
- `changed_files = ["file1.py", "logs/error.log", "temp.cache"]`
- `mergeable = True`
- `warnings` must equal:
  - `Detected runtime artifact: logs/error.log`
  - `Detected runtime artifact: temp.cache`

## Portability requirement
Allow configurable patterns for:
- protected files
- artifact paths
- allowed changed files

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- checker can identify at least:
  - valid scoped change
  - missing deliverable
  - runtime artifact
  - out-of-scope change
- implementation matches the normative semantics and examples above
