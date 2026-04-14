# Task 183 — orchestrator resume checkpoint and attempt state re-entry

## Why

The orchestrator now has meaningful partial-progress states, but interrupted or partially-green runs still need more precise re-entry truth so retries do not start too broadly or forget the last safe surface.

## Scope

Persist resume-safe attempt checkpoints and recovery re-entry truth.

## Runtime seams to reuse

- Reuse existing batch checkpoint and batch state truth.
- Reuse subset-preservation and rollback metadata where available.
- Reuse known-safe runtime-artifact retention behavior.
- Reuse task-admission truth for proof and re-proof tasks.

## Requirements

- Persist enough attempt state to distinguish:
  - fresh execution
  - retry after failure
  - resume after partial progress
  - manual intervention before resume
- Add resume checkpoints that record the last safe transition point and intended re-entry surface.
- Keep resume behavior conservative: when state is ambiguous or corrupted, prefer safe restart over unsafe optimistic resume.
- Add tests that cover at least one successful resume/re-entry path and one conservative fallback path.

## Create or update these exact files

- `agents/lib/attempt_state.py`
- `agents/lib/resume_state.py`
- `tests/test_attempt_state_resume.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/183_orchestrator_resume_checkpoint_and_attempt_state_reentry.md`

## Non-goals

- Do not promise arbitrary long-horizon workflow continuation.
- Do not weaken cleanup or branch-hygiene requirements.
- Do not bypass protected-surface checks on resume.

## Acceptance criteria

- Resume-safe checkpoints and re-entry truth exist and are persisted durably.
- Tests cover successful re-entry and safe conservative fallback.
- Docs explain that this is about reliability and lower broad-retry frequency, not broader autonomy.

## Implementation notes

- Prefer explicit serialized state objects and transition markers over implicit inference from scratch artifacts alone.

## Implementation snapshot (added)

- New helpers: `agents/lib/resume_state.py` (checkpoint objects) and `agents/lib/attempt_state.py` (persistence + conservative re-entry planner).
- Tests: `tests/test_attempt_state_resume.py` verifies one successful resume path (resume from a safe prechecks-passed checkpoint) and one conservative fallback path (manual intervention forces safe restart).
