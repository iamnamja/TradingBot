# Task 069 — Orchestrator controller decomposition second extraction

## Why this task exists

Tasks 068a–068c improved protected routing, duplicate-bundle handling, and began shrinking `agents/run_task.py`, but the controller still carries too much coordination logic inline.

If the orchestrator is going to execute many tasks in sequence, it cannot keep accumulating recovery, protected-lane, and control-plane logic inside one protected file.

## Outcome

Perform the second controller decomposition step by extracting higher-risk but still well-bounded controller logic into dedicated helper modules, while preserving the current public/helper surface and behavior.

This task should make the controller easier to evolve before batch/backlog execution is layered on top.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `agents/lib/protected_lane.py`
- `agents/lib/bundle_repair.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/orchestrator_extraction_plan.md`

## Required behavior

### 1) Extract protected-lane coordination helpers

Move narrow protected-lane orchestration helpers into `agents/lib/protected_lane.py`.

This extraction should include logic such as:

- identifying executable protected targets
- building the protected target profile for known controller files
- coordinating protected-lane request arguments
- reconciling protected accepted results back into the controller flow

Keep thin compatibility wrappers or imports in `agents/run_task.py` where tests already depend on the existing helper names.

### 2) Extract bundle-repair helpers

Move duplicate/conflicted-bundle recovery helpers into `agents/lib/bundle_repair.py`.

This extraction should include logic such as:

- duplicate bundle path classification
- equivalent-duplicate normalization
- conflicted-file focused repair request preparation
- duplicate-conflict durable artifact writing or delegation

### 3) Preserve shell-router parity

`agents/lib/shell_router.py` must consume the extracted helpers rather than keeping divergent local copies of the same logic.

### 4) Keep `run_task.py` thinner but stable

After extraction, `agents/run_task.py` should still coordinate the run and preserve the helper/public surface that current tests already use, but it should no longer own every implementation detail inline.

### 5) No regression in current reliability behaviors

Do not regress:

- protected-lane routing
- duplicate bundle recovery
- deliverable completeness enforcement
- truthful failure artifacts

## Tests

Add runtime-foundations coverage that proves:

1. extracted protected-lane helpers are used by both `run_task.py` and `shell_router.py`
2. extracted bundle-repair helpers preserve current duplicate/conflict behavior
3. compatibility wrappers in `agents.run_task` still satisfy current helper/public-surface expectations
4. decomposition measurably reduces direct controller responsibility without behavior drift

Keep the tests narrow and deterministic.

## Documentation

Update `docs/orchestrator_extraction_plan.md` to reflect that:

- protected-lane coordination is now extracted
- bundle-repair control-plane logic is now extracted
- `run_task.py` is thinner, but top-level orchestration still remains

## Guardrails

- Do not turn this into a broad redesign of every controller module
- Do not break existing tests by abruptly removing helper names from `agents.run_task`
- Prefer extracting cohesive helper groups rather than partial fragments with heavy back-references

## Acceptance

This task is complete when:

- protected-lane coordination lives in `agents/lib/protected_lane.py`
- duplicate/conflict bundle recovery lives in `agents/lib/bundle_repair.py`
- `run_task.py` and `shell_router.py` consume those helpers
- tests remain green
- the extraction plan clearly reflects the new controller shape
