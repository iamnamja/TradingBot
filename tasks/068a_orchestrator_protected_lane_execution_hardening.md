# Task 068a — Orchestrator protected lane execution hardening

## Why this task exists

Task 067a improved protected-file detection and made failure artifacts truthful, but recent execution history still shows a larger autonomy gap:

- protected meta harness tasks no longer fail with misleading artifact messages
- however, they still do not reliably *complete* through a working protected execution lane
- mixed tasks that include both protected and non-protected files can still stall before the protected portion is meaningfully executed

If the orchestrator is going to run a wide variety of tasks automatically, protected-controller work cannot remain a manual-only escape hatch.

## Outcome

When a task explicitly includes protected meta harness files, the orchestrator should be able to enter a real protected execution lane instead of treating protection as a terminal condition.

The first goal is not full generality. The goal is a narrow, deterministic controller path that can:

- keep protected files out of the normal file-bundle lane
- continue to allow normal non-protected files to use the normal lane
- compile and apply protected edits through a dedicated protected method path
- preserve existing validator / completeness / artifact behavior

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`

## Required behavior

### 1) Dedicated protected execution entry

Add a narrow controller path that is selected when the task contract or required deliverables explicitly include protected meta harness files.

That path should:

- partition protected and non-protected targets
- allow non-protected targets to remain in the normal bundle scope
- request protected changes through the protected method flow rather than the normal file-bundle flow
- keep current deliverable completeness checks intact

### 2) Mixed-task support

For tasks that include both protected and non-protected files:

- protected files must go through the protected lane
- non-protected files may still use the normal bundle lane
- the controller must be able to reconcile the final accepted result across both lanes before validators run

Do not require the entire task to collapse into a single lane if only part of the deliverable set is protected.

### 3) Narrow protected edit contract

The protected lane does not need a broad new language. It should remain conservative and machine-checkable.

At minimum it should support:

- explicit target file selection
- explicit method or symbol intent for the protected file(s)
- deterministic validation that the protected target set matches the task contract

### 4) Keep truthful failure artifacts

If protected execution still fails, the runtime must continue to write truthful artifacts and failure messages, including whether:

- protected execution was attempted
- only normal execution was attempted
- the task was mixed protected/non-protected
- protected targets were successfully identified before failure

### 5) No regression for normal tasks

Tasks with no protected deliverables must keep current behavior.

Do not regress:

- localized repair
- deliverable completeness enforcement
- truthful artifact persistence
- successful normal-bundle tasks

## Tests

Add narrow runtime-foundations coverage that proves:

1. a protected-only task enters the protected execution lane instead of the normal bundle lane
2. a mixed task can keep normal files in the normal lane while protected files go through the protected lane
3. final accepted-file accounting includes both protected and non-protected accepted results
4. truthful artifacts still exist when protected execution fails after routing
5. ordinary non-protected tasks keep current behavior

Keep the tests deterministic and avoid network or subprocess dependence beyond existing harness seams.

## Documentation

Update `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md` to describe:

- when the protected execution lane is used
- how mixed protected/non-protected tasks are routed
- what the current protected lane guarantees and does not guarantee
- that truthful failure artifacts remain required

## Guardrails

- Do not weaken the protected-file safety policy
- Do not collapse all mixed tasks into a manual-only path
- Do not replace explicit deliverable checks with fuzzy heuristics
- Prefer a narrow, test-backed lane implementation over a broad redesign

## Acceptance

This task is complete when:

- protected-only tasks no longer die immediately at the normal bundle gate
- mixed tasks can route protected and non-protected files through separate lanes
- accepted-file accounting remains correct across both lanes
- runtime-foundations tests pass
- the docs explain the protected execution lane clearly
