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

### Required checks
The checker must detect:
- missing deliverables
- unexpected extra changed files
- likely runtime artifacts such as:
  - files under `logs/`
  - generated cache/temp files

### Verdict
Return a structured verdict that includes:
- mergeable: true/false
- reasons
- warnings

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
