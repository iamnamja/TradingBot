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

## Create or update these exact files

- `agents/lib/attempt_state.py`
- `agents/lib/resume_state.py`
- `agents/lib/bounded_pilot.py`
- `tests/test_attempt_state_resume.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/198_orchestrator_adjacent_pair_resume_precision_and_checkpointed_reentry_truth.md`

## Non-goals

- Do not introduce unattended multi-task sequencing.
- Do not broaden beyond adjacent-pair resume precision.

## Acceptance criteria

- Resume artifacts distinguish precise re-entry from broad rerun behavior.
- Adjacent-pair re-entry is tested with representative partial-success cases.
- The bounded pilot remains compatible with the updated resume truth.
