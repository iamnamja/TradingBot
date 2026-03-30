# Task 068b — Orchestrator duplicate bundle normalization and focused repair

## Why this task exists

After protected routing improved, the next visible autonomy failure was a malformed model bundle that repeated the same `FILE:` path multiple times.

Today that failure is surfaced accurately, but it still hard-fails the task even when the orchestrator already has enough information to recover in a narrower, more targeted way.

This task hardens the controller against one of the most common malformed bundle shapes:

- duplicate file paths in a returned bundle

## Outcome

When the model returns a bundle with duplicate file paths, the orchestrator should not immediately abandon the task unless recovery is unsafe.

It should:

- normalize the bundle when the duplicates are safely equivalent
- or run a focused repair request for only the conflicted file(s)
- while preserving already accepted non-conflicted files

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/bundle_parser.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

### 1) Duplicate-path classification

Teach the parser/controller to distinguish between:

- exact duplicate file entries with equivalent content
- conflicting duplicate file entries with materially different content
- duplicate-path cases mixed with other valid non-conflicted files

Do not treat all duplicate-path bundles as equally fatal.

### 2) Safe normalization

If duplicate entries for the same file are byte-equivalent after existing normalization rules, the parser may collapse them into one accepted file entry.

This should be conservative and deterministic.

### 3) Focused conflicted-file repair

If duplicate entries for the same path are not safely equivalent, the controller should perform one focused repair attempt for only the conflicted file path(s), while preserving already accepted non-conflicted files.

That focused repair should:

- name the conflicted paths explicitly
- ask for only one final version per conflicted path
- avoid reopening unrelated already accepted files
- keep deliverable completeness enforcement active

### 4) Durable failure when conflict remains unresolved

If the conflicted file set still cannot be resolved after the focused repair attempt, fail the run with a durable artifact in repo root named:

- `last_output_duplicate_bundle_conflict.json`

That artifact should capture at least:

- task file
- conflicted paths
- accepted non-conflicted files
- whether normalization was possible
- whether focused repair was attempted
- short human-readable reason

### 5) No regression for ordinary malformed-bundle handling

Do not regress existing handling for:

- localized repair of small malformed bundles
- protected routing and truthful artifacts
- deliverable completeness enforcement
- non-duplicate malformed bundle categories

## Tests

Add narrow runtime-foundations coverage that proves:

1. byte-equivalent duplicate file entries can be normalized safely
2. conflicting duplicate file entries trigger a focused conflicted-file repair
3. already accepted non-conflicted files are preserved while conflicted files are retried
4. unresolved duplicate conflicts create the durable conflict artifact
5. non-duplicate malformed bundles keep current behavior

## Documentation

Update `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` to describe:

- how duplicate file paths are classified
- when safe normalization is allowed
- when the controller falls back to focused conflicted-file repair
- when the durable duplicate-conflict artifact is written

## Guardrails

- Do not silently choose one conflicting duplicate over another without a test-backed rule
- Do not reopen already accepted unrelated files during conflicted-file repair
- Do not weaken existing malformed bundle or protected-file controls

## Acceptance

This task is complete when:

- duplicate-path bundles no longer hard-fail when safe recovery is possible
- conflicted duplicate files trigger a focused repair rather than a blind rerun
- unresolved duplicate conflicts produce the durable artifact
- runtime-foundations tests pass
- the docs explain duplicate bundle recovery clearly
