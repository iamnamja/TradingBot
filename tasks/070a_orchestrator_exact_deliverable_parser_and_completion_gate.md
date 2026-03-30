# Task 070a — Orchestrator exact deliverable parser and completion gate hardening

## Why this task exists

Recent protected/controller continuation tasks exposed a trust gap in the current controller:

- the orchestrator can often repair code and return to green
- however, exact markdown deliverables under `docs/` can still be omitted even when the task explicitly names them
- operators are still catching these omissions by reviewing branch diffs after the run

That means the runtime is not yet fully aligned with the task contract style now used in the backlog.

If later backlog-execution work is going to be credible, the controller must stop treating exact-file documentation deliverables as optional.

## Outcome

Harden exact-deliverable parsing and completion enforcement so tasks that enumerate exact files fail closed when any required deliverable is omitted.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_contracts.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_contracts.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Broaden exact-deliverable section recognition

The task-contract parser must recognize exact-file sections used by the current backlog, including at minimum:

- `## Deliverables`
- `## Create or update these exact files`

The parser should remain deterministic and conservative.

### 2) Accept canonical repo-relative documentation/task paths

When a task enumerates exact files, the parser must accept narrow repo-relative paths under at least:

- `agents/`
- `src/`
- `tests/`
- `docs/`
- `tasks/`

It should also accept explicitly named canonical top-level files such as `README.md` when a task names them directly.

### 3) Reject unsafe or non-canonical paths

Do not allow the exact-deliverable parser to silently accept path traversal or malformed pseudo-paths.

Examples that should be rejected clearly include:

- `../outside.md`
- absolute filesystem paths
- URLs or prose that are not file paths

### 4) Fail closed when exact deliverables are omitted

When a task enumerates exact files, the run must not be considered complete if any required deliverable is missing from the accepted result.

At minimum, the failure message should make it obvious:

- which exact files were parsed from the task contract
- which required files were missing from the generated/accepted result
- whether the omission came from runtime output versus post-processing or lane reconciliation

### 5) Preserve current single-task and protected-lane behavior

Do not regress:

- ordinary task execution
- protected-lane routing
- duplicate-bundle repair
- truthful failure-artifact persistence

This task is about contract parsing and completion enforcement, not a broad controller redesign.

## Tests

Add coverage that proves:

1. exact-file lists are parsed from both supported heading styles
2. `docs/...` and `tasks/...` paths are treated as valid required deliverables
3. `README.md` can be accepted when explicitly listed
4. traversal or malformed paths are rejected clearly
5. a run with missing exact markdown deliverables fails completeness instead of quietly going green
6. existing protected and non-protected task behavior remains stable

## Documentation

Update the vision/controls and project-state docs to state that exact deliverable completeness now includes canonical documentation/task paths and is enforced by the controller rather than only by operator diff review.

## Guardrails

- Do not weaken protected-file safety rules
- Do not replace exact-file enforcement with fuzzy heuristics
- Do not treat docs deliverables as advisory when the task lists them explicitly
- Prefer narrow, test-backed parsing/enforcement changes over a broad prompt rewrite

## Acceptance

This task is complete when:

- the task-contract parser recognizes the current exact-file section styles
- canonical documentation/task paths are accepted as exact deliverables
- omitted exact markdown deliverables fail the run clearly
- tests remain green
