# Task 017: Failure classifier

## Goal
Build a failure classifier that categorizes failed task runs and recommends the next orchestration action.

## Deliverables
- `src/builder/orchestrator/failures.py`
  - failure categories
  - classifier logic

- `tests/test_failure_classifier.py`

## Required behavior
### Categories
Support at least:
- implementation_bug
- task_ambiguity
- runner_weakness
- ci_dependency_issue
- repo_hygiene_issue
- unknown

### Inputs
Classifier should be able to examine:
- task runner output
- lint/test failure text
- optional changed-file info

### Required examples
The classifier should identify patterns such as:
- missing required deliverables
- invented import/module path issues
- CI missing dependency/package
- runtime artifact committed
- repeated semantic assertion mismatches

### Output
Return structured output including:
- category
- confidence or rationale
- recommended next action:
  - retry_task
  - patch_task
  - patch_runner
  - patch_ci
  - clean_repo
  - require_human_review

## Acceptance criteria
- `ruff check .` passes
- `pytest -q` passes
- classifier is deterministic for the provided examples
