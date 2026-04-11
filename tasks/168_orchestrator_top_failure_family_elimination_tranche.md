# Task 168 — orchestrator top failure family elimination tranche

## Why

Once the scorecard and authority corroboration are tightened, the next priority is not another generic feature. It is to reduce the single most common real failure family still showing up in one-task autonomous runs.

## Scope

Use the latest benchmark and re-proof artifacts to identify the dominant current one-task failure family, then land the narrowest fix that measurably reduces that family without widening scope.

## Requirements

- Use measured benchmark or re-proof artifacts as the basis for choosing the target failure family.
- Name the chosen failure family explicitly in task outputs and docs.
- Keep the fix narrow and tied to the dominant failure class.
- Preserve compatibility seams and public surfaces unless there is a compelling measured reason to change them.
- Update artifacts or docs so the before/after effect is visible.

## Acceptance criteria

- The chosen failure family is named explicitly.
- Tests prove the targeted fix for that family.
- Updated artifacts or project-state notes show the failure family is reduced or better classified.
