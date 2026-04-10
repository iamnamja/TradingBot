# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, `tests`, and `README.md` snapshots as the source of truth.

## Current completed state

- synchronized continuation is complete through **Task 154**
- the repo has a bounded supervised slice plus a narrow autonomous one-task lane
- Tasks **149–154** completed the one-task execution-quality proving tranche:
  - 149 external-safe corpus and evaluation manifest
  - 150 one-task multi-agent dev / test / repair / controller loop
  - 151 external-safe failure taxonomy and self-heal router
  - 152 one-task pass-rate scoreboard and failure digest
  - 153 external-safe corpus reliability re-proof
  - 154 two-task readiness gate and phase transition

## Important reality

- the repo can honestly claim only **one allowlisted safe task at a time** under supervision
- Task 154 added an explicit widening gate, but it did **not** widen the lane
- the current truthful result is still **no-go** for bounded two-task trials
- self-hosting control-plane work remains escalation-first unless separately proven safe
- broad unattended scheduler autonomy is still not an honest claim

## Current widening gate

Bounded two-task trials are allowed only when the one-task external-safe lane clears all of these thresholds:

- at least **6** evaluated runs
- at least **0.75** completion rate
- at most **0.25** escalation rate
- at most **0.10** hosted-authority block rate
- at most **0.34** self-healed completion share
- direct completions must exceed self-healed completions

The current measured posture remains below that bar: the latest external-safe re-proof band is roughly **4 of 6** completed, with **2 of 4** completions still requiring bounded self-heal.

## Agreed phase order

1. make one-task autonomous execution work reliably on ordinary external-safe tasks
2. only then widen into bounded two-task execution
3. only later package the orchestrator as its own operator-facing app
4. self-hosting app work is a later privilege, not the current proving ground

## Working style

- use `tasks/README.md` as canonical task ordering
- keep the lane narrow and operationally honest
- do not widen claims beyond what tests and measured artifacts support
- exact deliverable completeness matters
- run focused validation first, then `ruff check .`, then `pytest -q`
- preserve compatibility seams and stable exports in `agents/run_task.py`
- prefer the smallest targeted recovery when a task branch is close
- do not broaden autonomy claims unless the explicit gate is both implemented and green in measured artifacts

## What should happen next

Unless new evidence clearly clears the widening gate, the next task tranche should continue improving **one-task execution quality** rather than starting bounded two-task rollout work.
