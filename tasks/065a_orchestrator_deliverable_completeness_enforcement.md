# Task 065a — Orchestrator deliverable completeness enforcement

## Why this task exists

Tasks 064 and 065 showed that the orchestrator can produce a validator-green result while only updating a subset of the files explicitly required by the task. This is a real control gap: passing `ruff` / `pytest` is necessary, but it is not sufficient when a task contract explicitly names exact deliverable files.

We need the orchestrator runtime to enforce task completeness when the task text clearly says which files must be created or updated.

## Outcome

When a task explicitly enumerates exact deliverable files, the final accepted result must include all of them. If one or more required files are missing, the run must not be marked green. The controller should either perform a focused follow-up repair for the missing files or fail with a durable artifact.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

### 1) Conservative deliverable extraction

Add a conservative helper in `agents/run_task.py` that extracts required deliverable paths from task text only when the task clearly provides an explicit file list.

Accept only clear patterns such as headings like:

- `Create or update these exact files`
- `Deliverables`
- `Files`
- `Required files`

And only collect repo-relative paths that appear in backticks and look like real file paths.

Do **not** infer required files from vague prose.

### 2) Final completeness check

After the controller has an accepted result bundle and validators pass, compute the final changed/accepted file set using the union of:

- normal file-bundle paths
- protected method-edit target files
- files preserved from partial bundle salvage
- files accepted through localized repair

If the task declared required deliverables and any required file is missing from that final accepted set, do **not** mark the run green.

### 3) Focused repair for missing deliverables

If the only remaining issue is missing required deliverable files, trigger one focused repair attempt that asks only for the missing files while preserving already accepted files.

The focused repair should:

- name the missing file paths explicitly
- preserve already accepted files
- avoid reopening unrelated files
- re-run normal validators after the repair is applied

### 4) Durable failure on unresolved incompleteness

If required deliverables are still missing after the focused repair attempt, fail the run and write a durable artifact in repo root named:

- `last_output_deliverable_completeness_failure.json`

That artifact should capture at least:

- task file
- required deliverables
- accepted files
- missing deliverables
- whether a focused repair was attempted

### 5) No enforcement when the task is ambiguous

If the task text does not contain an explicit deliverable file list in one of the supported patterns, do not apply completeness enforcement. Existing behavior should remain unchanged.

## Tests

Add runtime-foundations coverage that proves:

1. explicit required deliverables are extracted from supported task text
2. a missing required file blocks a green result and triggers a focused repair
3. already accepted files are preserved while only missing files are requested
4. unresolved missing deliverables create the durable failure artifact
5. ambiguous task text does not trigger completeness enforcement

Keep the tests narrow and deterministic.

## Documentation

Update `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` to describe:

- when deliverable completeness enforcement applies
- that it is conservative and only enabled for explicit file lists
- that validator-green is not sufficient when explicit deliverables are missing
- that the controller may run a focused missing-file repair before failing

## Guardrails

- Preserve current localized-repair behavior for malformed bundles and protected-file flows
- Do not require diff-based artifacts
- Do not broaden task parsing into fuzzy file inference
- Keep the implementation backward-compatible with the current public helper surface unless a test-backed change is necessary

## Acceptance

This task is complete when:

- explicit deliverable lists are enforced
- partial task implementations like 064/065 would no longer be marked green
- one focused missing-file repair is attempted before failure
- unresolved incompleteness produces the durable failure artifact
- runtime-foundations tests pass
