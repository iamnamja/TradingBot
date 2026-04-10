# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, and `tests` snapshots as the source of truth.

## Current completed state

- synchronized continuation is complete through **Task 155**
- the repo has a bounded supervised slice plus a narrow autonomous one-task lane
- Tasks 149–154 completed the execution-quality tranche:
  - 149 external-safe corpus and evaluation manifest
  - 150 one-task multi-agent dev / test / repair / controller loop
  - 151 external-safe failure taxonomy and self-heal router
  - 152 one-task pass-rate scoreboard and failure digest
  - 153 external-safe corpus reliability re-proof
  - 154 two-task readiness gate and phase transition
- Task 155 begins the blocker-reduction follow-up tranche:
  - bounded safe lint preflight normalization for isolated lint-only failures on required Python paths

## Important reality

- the repo can honestly claim only **one allowlisted safe task at a time** under supervision
- Task 154 added an explicit go / no-go gate, and the current truthful answer is still **no-go** for bounded two-task widening
- self-hosting control-plane work remains escalation-first unless separately proven safe
- broad unattended scheduler autonomy is still not an honest claim

## Agreed phase order

1. make one-task autonomous execution work reliably on ordinary external-safe tasks
2. only then widen into bounded multi-task execution
3. only later package the orchestrator as its own operator-facing app
4. self-hosting app work is a later privilege, not the current proving ground

## Current next-step posture

Because the Task 154 gate is still red, the next work should reduce one-task blockers instead of widening the lane. That means:

- remove preventable lint-only failures where safe
- improve hosted-authority corroboration without weakening claim discipline
- reduce repair-heavy completions relative to direct completions
- only re-evaluate the two-task gate on fresh measured evidence

## Working style

- use `tasks/README.md` as canonical task ordering
- keep the lane narrow and operationally honest
- do not widen claims beyond what tests and measured artifacts support
- exact deliverable completeness matters
- run focused validation first, then `ruff check .`, then `pytest -q`
- preserve compatibility seams and stable exports in `agents/run_task.py`
- prefer the smallest targeted recovery when a task branch is close
