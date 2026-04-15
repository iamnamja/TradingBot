# Task 198 — orchestrator adjacent-pair resume precision and checkpointed re-entry truth

## Why

The recovered runtime path is useful only if partially-successful adjacent-pair runs re-enter precisely instead of broad reruns.

## Scope

Tighten adjacent-pair resume precision and persist clearer checkpointed re-entry truth.

## Runtime seams to reuse

- Reuse attempt-state and resume-state foundations.
- Reuse bounded two-task pair ledger and transport-health artifacts.
- Reuse conservative resume-truth style from earlier reliability tasks.

## Requirements

- Distinguish precise checkpoint re-entry from broad rerun behavior.
- Persist a small adjacent-pair resume-truth artifact or ledger extension.
- Keep the implementation additive and compatible with the bounded pilot runner.
- Add tests for representative partial-success and re-entry scenarios.

## Implementation notes

- Attempt-state re-entry planning now includes a precision field:
  - precision: precise when resuming from a safe checkpoint with a clear surface
  - precision: broad when restarting/fresh or resuming is unsafe/ambiguous
- The bounded two-task pilot persists a small resume_truth section in the pair ledger:
  - { mode, precision, source }, where source is task_payload when provided, otherwise inferred.
- All behavior is additive; existing ledger fields and attempt-state semantics remain stable.

## Acceptance criteria

- Resume artifacts distinguish precise re-entry from broad rerun behavior.
- Adjacent-pair re-entry is tested with representative partial-success cases.
- The bounded pilot remains compatible with the updated resume truth.
