# Task 067a — Orchestrator protected method mode routing and failure artifact persistence

## Why this task exists

Recent tasks showed two linked controller problems:

1. Tasks that explicitly require protected meta harness files such as `agents/run_task.py` and `agents/lib/shell_router.py` still enter the normal bundle lane and fail immediately with a protected-file policy error instead of being routed into a working protected method flow.
2. On that protected-file failure path, the runtime prints that `_last_agent_model_output.txt` and `_last_agent_file_bundle.txt` were saved even when those files were never actually written.

This makes protected-file tasks harder to debug and forces repeated manual patch intervention even when the controller already knows the task requires protected files.

## Outcome

When a task explicitly requires protected meta harness files, the controller must not attempt the normal file-bundle lane for those files. It must either:

- route them through a working protected method flow, while still allowing normal non-protected file bundle generation for the remaining files, or
- fail early with real persisted debugging artifacts that accurately describe what happened.

Also, the runtime must never claim that `_last_agent_model_output.txt` or `_last_agent_file_bundle.txt` were saved unless those files were actually written.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

### 1) Protected deliverable pre-routing

Add a narrow controller helper that determines whether the current task explicitly requires one or more protected meta harness files.

Use only conservative signals already available in the task contract / required-file parsing flow. Do not introduce fuzzy heuristics.

If the required deliverable set includes protected meta harness files, do not pass those files into the normal bundle lane. Instead:

- keep them in the protected-file set
- keep non-protected required files eligible for the normal file-bundle lane
- avoid the immediate meta-file gate failure for the full task when the task is otherwise valid

### 2) Accurate failure artifact persistence

Whenever the runtime prints either of these messages:

- `Model output saved to: _last_agent_model_output.txt`
- `Parsed file bundle saved to: _last_agent_file_bundle.txt`

it must be true that the referenced file exists on disk after the failure path returns.

If there is no model output yet because the run failed before the first model call, write a truthful placeholder artifact rather than claiming that a real model response was saved.

For `_last_agent_file_bundle.txt`, write a truthful placeholder or machine-readable failure note when no parsed file bundle exists.

### 3) Truthful protected-file failure artifacts

When protected-file routing still fails, the persisted artifacts should make the failure diagnosable.

At minimum they should capture:

- task file
- failure category
- protected files involved
- whether the failure happened before any model output was received
- whether a normal bundle was attempted
- a short human-readable reason

### 4) Keep current normal-task behavior intact

Do not regress successful normal bundle tasks.

Tasks with no protected deliverables should behave exactly as they do now, including localized repair and deliverable completeness enforcement.

### 5) Preserve current public helper surface unless a test-backed change is required

Any new helper introduced in `agents/run_task.py` or `agents/lib/shell_router.py` should remain internal unless a stable exported seam is clearly needed.

## Tests

Add narrow runtime-foundations coverage that proves:

1. a task whose required deliverables include protected files does not feed those files into the normal bundle lane
2. non-protected files can still remain in the normal bundle scope for the same task
3. when the failure path prints that `_last_agent_model_output.txt` and `_last_agent_file_bundle.txt` were saved, those files actually exist
4. placeholder artifacts are written when the failure occurs before any model output or parsed bundle exists
5. ordinary non-protected tasks keep their current behavior

Keep the tests deterministic and avoid network or subprocess dependence beyond existing harness seams.

## Documentation

Update `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` to describe:

- that protected meta harness deliverables are pre-routed out of the normal bundle lane
- that normal non-protected deliverables may still use the normal bundle lane in the same task
- that failure artifact messages must be truthful and correspond to files actually written
- that placeholder artifacts may be written when failure occurs before any model output exists

## Guardrails

- Do not remove or weaken the protected-file policy gate
- Do not broaden task parsing into fuzzy protected-file inference
- Do not regress localized repair, deliverable completeness enforcement, or current successful normal-bundle runs
- Prefer a narrow controller/routing fix over a broad redesign

## Acceptance

This task is complete when:

- explicit protected deliverables no longer cause an immediate misleading normal-bundle failure for otherwise valid mixed tasks
- protected-file failure messages correspond to real persisted artifact files
- the new tests pass
- the docs explain the protected pre-routing and truthful artifact policy
