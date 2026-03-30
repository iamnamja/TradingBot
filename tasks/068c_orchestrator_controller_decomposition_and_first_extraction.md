# Task 068c — Orchestrator controller decomposition and first extraction

## Why this task exists

The current orchestrator can sometimes complete normal tasks, but protected/controller work still tends to require manual intervention, and repeated fixes keep colliding inside `agents/run_task.py`.

That file still carries too many responsibilities at once:

- task contract parsing
- deliverable completeness policy
- canonical docs path policy
- truthful failure-artifact writing
- bundle request / retry coordination
- protected routing decisions
- top-level shell control flow

If the orchestrator is going to run a variety of tasks automatically, the controller must become easier to reason about and safer to edit.

## Outcome

Perform the first real decomposition step so `agents/run_task.py` becomes thinner and more stable.

This task should extract pure helper logic into dedicated modules while keeping the public behavior and existing helper surface intact.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `agents/lib/task_contracts.py`
- `agents/lib/failure_artifacts.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/orchestrator_extraction_plan.md`

## Required behavior

### 1) Extract task-contract helpers

Move pure task-contract and deliverable-policy helpers into `agents/lib/task_contracts.py`.

This extraction should include logic such as:

- explicit deliverable parsing
- canonical docs path policy checks
- protected/non-protected required-path partitioning
- task-scope broadness signals that do not require live execution state

Keep the thin wrappers or imports in `agents/run_task.py` stable where tests already depend on them.

### 2) Extract truthful failure-artifact helpers

Move placeholder / durable artifact writing and related helper logic into `agents/lib/failure_artifacts.py`.

This should include:

- truthful `_last_agent_*` placeholder writing
- machine-readable failure artifact writing helpers
- shared message formatting used by `run_task.py` and `shell_router.py`

### 3) Keep `run_task.py` as a thinner orchestrator shell

After extraction, `agents/run_task.py` should still coordinate the run, but it should no longer own every pure helper directly.

The goal is not to finish decomposition in one task. The goal is to make the controller clearly thinner and safer to evolve.

### 4) Preserve shell-router parity

`agents/lib/shell_router.py` should consume the extracted helpers rather than drifting from `agents/run_task.py`.

Avoid duplicating the same helper logic in both places.

### 5) Preserve public helper compatibility where already depended on

If tests or current runtime behavior rely on specific internal helper names being present in `agents.run_task`, keep thin compatibility wrappers or aliases rather than breaking them abruptly.

## Tests

Add runtime-foundations coverage that proves:

1. extracted task-contract helpers are used by the controller without changing existing behavior
2. extracted failure-artifact helpers are shared by both `run_task.py` and `shell_router.py`
3. compatibility wrappers in `agents.run_task` still satisfy current public-surface tests
4. decomposition reduces direct helper implementation in `run_task.py` without regressing behavior

Keep the tests narrow and deterministic.

## Documentation

Update `docs/orchestrator_extraction_plan.md` to reflect that:

- a first controller extraction has landed
- `run_task.py` is still not fully decomposed
- the next extraction priorities are the protected execution lane and bundle-repair/control-plane logic if they remain too entangled

## Guardrails

- Do not turn this into a broad multi-module redesign
- Do not break the current public/helper surfaces abruptly
- Prefer extracting pure helper logic first, leaving orchestration flow in place
- Keep the change small enough to validate confidently

## Acceptance

This task is complete when:

- `run_task.py` is measurably thinner in responsibility
- pure task-contract and failure-artifact helpers live in dedicated modules
- shell-router and run-task share those helpers instead of duplicating logic
- existing tests remain green
- the extraction plan doc reflects the new controller shape
