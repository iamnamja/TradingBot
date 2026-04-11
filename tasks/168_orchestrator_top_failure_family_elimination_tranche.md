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

## Create or update these exact files
- agents/run_task.py
- tests/test_run_task_parsers_and_policies.py
- tests/test_failure_journal.py
- tasks/168_orchestrator_top_failure_family_elimination_tranche.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- The chosen failure family is named explicitly.
- Tests prove the targeted fix for that family.
- Updated artifacts or project-state notes show the failure family is reduced or better classified.

---

## Chosen dominant failure family

Based on the latest strict benchmark and re-proof artifacts, the dominant remaining one-task failure family has been:

- failure family: missing_failure_artifact_placeholders
- description: runs that fail before or during model-output parsing occasionally left _last_agent_model_output.txt or _last_agent_file_bundle.txt missing or containing non-JSON/partial content, causing brittle resume behavior and under-classified failures.

This family surfaced as the most frequent cause of “unclassified or stale-artifact” single-task failures after earlier transport and scorecard gates were tightened.

## Targeted, narrow fix

We hardened the failure-artifact reporter in agents/run_task.py:

- Change: _emit_failure_artifact_messages now deterministically writes canonical JSON placeholders whenever create_placeholders=True (including pre-output failures), overwriting any stale or non-JSON files.
- Guarantee: the reporter never raises, and always persists batch_checkpoint/batch_state annotations so downstream components can classify the failure reliably, even when no model bundle was produced.
- Guardrail parity: the partition helper continues to exclude protected meta harness files (e.g., agents/run_task.py) from the normal bundle, so protected-method edits cannot leak into the ordinary bundle lane.

The fix is strictly localized to failure artifact writing and does not widen runner behavior or public surfaces.

## Tests

- We added focused tests to assert that:
  - placeholder artifacts are created and overwrite stale text on pre-output failures.
  - existing JSON artifacts are annotated safely without crashes.
  - protected meta harness files (e.g., agents/run_task.py) are excluded from the normal bundle by the partition helper.

Concretely:
- tests/test_failure_journal.py::test_failure_artifact_placeholders_include_artifact_kind_and_checkpoint
- tests/test_run_task_parsers_and_policies.py::test_partition_required_paths_excludes_meta_harness_files_from_normal_bundle

These tests validate the behavior that eliminates the chosen failure family without altering unrelated orchestrator flows.

## Before / After visibility

- Before: runs could leave absent or malformed failure-artifact files after early/pre-output failures, obscuring classification and resume paths.
- After: artifacts are always present, valid JSON, and annotated with checkpoint/state truth. Failures are better classified and visible to downstream consumers.

## Scope honesty

The change is intentionally narrow:

- No change to acceptance scoring, task routing, or controller surfaces.
- Only the failure-artifact reporter semantics were strengthened to write canonical placeholders deterministically.

This should measurably reduce the missing_failure_artifact_placeholders family while preserving the established compatibility boundaries.
