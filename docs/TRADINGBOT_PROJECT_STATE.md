# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (src/tradingbot)
- Orchestrator engine and control plane (src/builder/orchestrator)
- Agent execution harness (agents)
- Numbered implementation tasks (tasks)
- Documentation and project-state tracking (docs)

## Current state (post-Task 168)

- Tasks 124–167 are complete in bounded supervised scope: the repo freezes public/tested compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes malformed and empty bundle failures, preserves last-known-good subsets during retries, maintains bounded autonomous one-task execution, adds benchmark scorecard integration, improves authority-gate evidence handling, hardens deliverable contracts and completion prompts, normalizes runtime artifact hygiene, completes a second one-task reliability re‑proof, moves benchmark decisions onto a strict no‑manual‑intervention scorecard, and records explicit hosted‑authority corroboration state at benchmark time.
- Task 168 targets the dominant remaining one‑task failure family and lands the narrowest fix:

  - Dominant failure family (named): missing_failure_artifact_placeholders
  - Symptom: early/pre‑output failures sometimes left _last_agent_model_output.txt or _last_agent_file_bundle.txt missing or with non‑JSON/partial content, causing brittle resume behavior and under‑classified failures.
  - Fix: the failure‑artifact reporter deterministically writes canonical JSON placeholders with batch_checkpoint/batch_state annotations whenever create_placeholders=True, overwriting any stale/non‑JSON artifacts. The helper is resilient and never raises.
  - Guardrails preserved: protected meta harness files (e.g., agents/run_task.py) remain excluded from the normal bundle via the partitioner, keeping the protected‑method lane isolated.

## Evidence and tests

- New tests proving the fix:
  - tests/test_failure_journal.py::test_failure_artifact_placeholders_include_artifact_kind_and_checkpoint — validates deterministic JSON placeholders and checkpoint/state annotations.
  - tests/test_run_task_parsers_and_policies.py::test_partition_required_paths_excludes_meta_harness_files_from_normal_bundle — validates protected meta harness exclusion in the normal bundle lane.

- Expected effect: reduced rate of unclassified or stale‑artifact failures in one‑task autonomous runs. Failures are better surfaced and classified, improving resume and remediation planning.

## Scope honesty

- We did not widen orchestrator behavior or public surfaces.
- The change is narrowly scoped to failure‑artifact emission and bundle partitioning guarantees.
- The strict scorecard and hosted‑authority corroboration model remain unchanged and continue to gate promotion decisions.

## Next steps

- Continue tracking the strict scorecard to verify the measured reduction in the missing_failure_artifact_placeholders family.
- If residual top failures shift, repeat the tranche process with the same narrow, compatibility‑preserving posture.
