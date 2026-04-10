# Task 159 — orchestrator top failure family elimination tranche

## Why

Once the benchmark harness is running, the next priority is not more generic features. It is eliminating the single most common real failure family that shows up in autonomous one-task trials.

## Scope

Use the benchmark scorecard and failure digest to identify the dominant current one-task failure family, then land the narrowest fix that reduces that family without widening scope.

## Requirements

- The task must use measured benchmark artifacts as the basis for choosing the target failure family.
- The fix must be narrow and explicitly tied to the dominant failure class.
- The change must preserve compatibility seams and public surfaces unless there is a compelling measured reason to change them.
- The task must update benchmark/re-proof artifacts so the before/after effect is visible.

## Acceptance criteria

- The chosen failure family is named explicitly in task outputs/docs.
- Tests prove the targeted fix for that family.
- Updated artifacts show the failure family is reduced or better classified.
