# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, `tests`, and `README.md` snapshots as the source of truth.

## Current completed state

- synchronized continuation is complete through **Task 142**
- the repo now has a bounded supervised slice plus a narrow autonomous one-task lane
- key recent milestones:
  - 137 real GitHub required-check convergence around the stable `ci-required` contract
  - 138 safe task-family autonomy allowlist
  - 139 dedicated autonomous single-task runner and ledger
  - 140 canary metrics and recovery reporting
  - 141 escalation artifact and supervised handoff lane
  - 142 supervised safe-lane single-task re-proof

## Important reality

- the repo can honestly claim only **one allowlisted safe task at a time** under supervision
- self-hosting control-plane work remains escalation-first unless separately proven safe
- broad unattended scheduler autonomy is still not an honest claim
- the next tranche should focus on operational safe-lane convergence, not on widening autonomy claims

## Current live GitHub reality

- the stable hosted-authority contract is `ci-required`
- the GitHub ruleset for `main` should require `ci-required`
- the repo also publishes workflow/check-run surfaces such as `ci`
- the next tranche should harden interpretation of live PR reporting so the orchestrator distinguishes initial reporting delay from genuinely missing required-check evidence

## Next intended tranche

- 143 GitHub settle window and dual-surface probe
- 144 real PR required-check smoke proof
- 145 scheduler bridge to safe single-task runner
- 146 safe-lane stop/requeue and supervised mix policy
- 147 single-task resume and idempotent re-entry
- 148 live canary corpus and operator proof bundle

## Working style

- use `tasks/README.md` as canonical task ordering
- keep the lane narrow and operationally honest
- do not widen claims beyond what tests and live GitHub evidence support
- exact deliverable completeness matters
- run focused validation first, then `ruff check .`, then `pytest -q`
- preserve compatibility seams and stable exports in `agents/run_task.py` and `agents/lib/shell_router.py`
- prefer the smallest targeted recovery when a task branch is close

## Execution posture for this tranche

- 143–144 are operational/manual-first because they touch live GitHub hosted-authority truth
- 145–147 should remain bounded, one-task-only, and conservative
- 148 is the first operator-facing proof bundle for the live one-task canary lane
