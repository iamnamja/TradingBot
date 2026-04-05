# Task 081 — Orchestrator controller decomposition third extraction

## Why this task exists

The 069–080 work should make the orchestrator much more capable, but unless the new controller responsibilities are extracted, `agents/run_task.py` will remain too monolithic for long-term maintainability and autonomy.

This task is where the next real thinning pass happens.

## Outcome

Extract the batch executor, final acceptance reviewer, and git workflow controller helpers further out of `agents/run_task.py`, preserving public/runtime compatibility.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/batch_executor.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/git_workflow.py`
- `docs/orchestrator_extraction_plan.md`
- `tests/test_run_task_runtime_foundations.py`

## Required behavior

### 1) Thin run-task shell further

Keep `agents/run_task.py` as the orchestration shell and compatibility surface, but move reusable logic out where practical.

### 2) Extract three controller families

At minimum, extract or consolidate:

- batch executor/controller loop
- final acceptance review/report logic
- accepted-task PR/merge/reset workflow helpers

### 3) Preserve public/runtime surface

Existing wrapper/helper entrypoints expected by tests and normal runtime should remain available.

### 4) Honest extraction plan update

Update the extraction plan to describe what is now extracted and what still remains inline.

## Tests

Add/update coverage that proves:

1. public/runtime compatibility remains intact
2. extracted helpers are actually invoked by the shell
3. no behavior regressions are introduced by the extraction

## Documentation

Update the extraction plan to reflect the third controller-decomposition pass and its next remaining inline responsibilities.

## Guardrails

- Do not use this task as an excuse for broad feature redesign
- Preserve current behavior while moving logic out of the monolithic shell
- Prefer small, explicit extractions over giant rewrites

## Acceptance

This task is complete when:

- `agents/run_task.py` is materially thinner again
- extracted helpers own the new controller responsibilities
- runtime/test compatibility remains intact
- extraction-plan docs are updated honestly
