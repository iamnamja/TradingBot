# Task 185 — orchestrator reliability checkpoint and capability resume gate

## Why

After Tasks 181–184, the repo needs another honest checkpoint: has runtime reliability improved enough to reopen cautious capability widening, or should the project continue reliability-first hardening?

## Scope

Record an explicit post-reliability checkpoint and capability-resume gate.

## Runtime seams to reuse

- Reuse reliability artifacts from Task 184.
- Reuse one-task and bounded two-task benchmark and promotion artifacts.
- Reuse supervised-intervention truth, failure-family truth, and resume/re-entry truth from the reliability tranche.
- Reuse the existing conservative checkpoint style already present in the repo.

## Requirements

- Produce a durable checkpoint that states whether the repo is:
  - not ready to resume capability widening,
  - conditionally ready under supervision,
  - or ready to resume cautious bounded capability widening.
- The checkpoint must explicitly evaluate:
  - recurring failure-family reduction,
  - retry-count improvement,
  - supervision/intervention rate,
  - compatibility-regression reduction,
  - resume-safe recovery behavior.
- Keep the verdict conservative:
  - broad unattended multi-task autonomy remains blocked,
  - standalone productization remains blocked,
  - reopening capability widening only means a cautious bounded next slice may be planned.

## Create or update these exact files

- `src/builder/orchestrator/reliability_benchmark.py`
- `tests/test_reliability_benchmark.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/185_orchestrator_reliability_checkpoint_and_capability_resume_gate.md`

## Non-goals

- Do not claim broad multi-task autonomy.
- Do not unblock standalone orchestrator-app work.
- Do not skip directly to arbitrary scheduling or open-ended role routing.

## Acceptance criteria

- A durable reliability checkpoint artifact exists.
- Docs state clearly whether capability widening may resume, and if so only cautiously and in bounded scope.
- Blocked areas remain explicit.
- Scope honesty is preserved.

## Implementation notes

- Keep the checkpoint additive and conservative, similar in tone to the bounded-corpus checkpoint.
- Artifact: `reliability/reliability_checkpoint.json` produced via the reliability benchmark module.
- Public surface: new helpers
  - `evaluate_reliability_resume_gate(matrix, previous_matrix=None, thresholds=None)`
  - `write_reliability_checkpoint(base_dir, evaluation, matrix_snapshot=None)`
- Default gate verdict (without previous improvement evidence): `conditional_under_supervision`.
