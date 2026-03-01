# Task 010: End-to-end cycle + logging/audit

## Goal
Create a single “cycle” runner that:
- checks market hours
- fetches data
- builds candidates
- LLM approve/veto
- risk gate
- execute (or dry-run)
- writes an audit log per cycle

## Scope
- `CycleRunner.run_once()` that returns a structured result
- Log format: JSON lines or a single JSON per run saved under `logs/`
- Include:
  - timestamp
  - config snapshot (safe fields only)
  - candidates
  - llm decisions
  - risk decisions
  - execution results

## Acceptance Criteria
- Produces one audit entry per run under `logs/`
- CI passes

## Tests
- Integration-ish test with mocks verifying call order + audit output created