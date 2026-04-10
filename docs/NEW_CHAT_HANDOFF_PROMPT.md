# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, `tests`, and `README.md` snapshots as the source of truth.

## Current completed state

- synchronized continuation is complete through **Task 148**
- the repo now has a bounded supervised slice plus a narrow autonomous one-task lane
- key recent milestones:
  - 143 GitHub settle window and dual-surface probe
  - 144 real PR required-check smoke proof
  - 145 scheduler bridge to safe single-task runner
  - 146 safe-lane stop/requeue and supervised mix policy
  - 147 single-task resume and idempotent re-entry
  - 148 live canary corpus and operator proof bundle

## Important reality

- the repo can honestly claim only **one allowlisted safe task at a time** under supervision
- self-hosting control-plane work remains escalation-first unless separately proven safe
- broad unattended scheduler autonomy is still not an honest claim
- the next phase should optimize for execution quality, not for more orchestration surface area

## Agreed phase order

1. make one-task autonomous execution work reliably on ordinary external-safe tasks
2. only then widen into bounded multi-task execution
3. only later package the orchestrator as its own operator-facing app
4. self-hosting app work is a later privilege, not the current proving ground

## Next intended tranche

- 149 external-safe corpus and evaluation manifest
- 150 one-task multi-agent dev / test / repair / controller loop
- 151 external-safe failure taxonomy and self-heal router
- 152 one-task pass-rate scoreboard and failure digest
- 153 external-safe corpus reliability re-proof
- 154 two-task readiness gate and phase transition

## Working style

- use `tasks/README.md` as canonical task ordering
- keep the lane narrow and operationally honest
- do not widen claims beyond what tests and measured artifacts support
- exact deliverable completeness matters
- run focused validation first, then `ruff check .`, then `pytest -q`
- preserve compatibility seams and stable exports in `agents/run_task.py` and `agents/lib/shell_router.py`
- prefer the smallest targeted recovery when a task branch is close
