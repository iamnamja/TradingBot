# TradingBot Project State

## Repository scope

The repository combines:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through reliability/autonomy continuation and conservative batch execution hardening.

Recent tranche highlights include:

- task-list manifest + queue model
- persisted batch state and deterministic resume groundwork
- conservative batch CLI and summary artifacts
- final acceptance reviewer + targeted acceptance self-heal
- dedicated sequential batch executor/controller loop (078) as canonical manifest execution surface
- **accepted-task autonomous PR/check/merge + clean-main reset gate (079)**

## Current state

The orchestrator now has an explicit per-task sequential controller loop that:

1. runs task execution
2. runs authoritative validation
3. runs final acceptance review
4. retries self-heal only when acceptance is retryable and budget remains
5. persists explicit terminal task outcome details
6. for accepted tasks, can optionally run PR/create/check/merge and enforce clean-main reset before next task
7. advances or stops conservatively

Conservative stop behavior is explicit and tested:

- `manual_patch` stops the loop
- `blocked` stops the loop
- PR/CI/merge/reset failure in autonomous merge posture stops honestly and prevents advancement

Accepted tasks continue only when all enabled gates pass.

## Canonical batch execution path

Canonical path for sequential manifest execution is now:

- `agents/lib/batch_executor.py` loop + `agents/lib/batch_state.py` persisted state/checkpoints + `agents/lib/task_queue.py` queue model/decisions + `agents/lib/git_workflow.py` accepted-task PR/merge/reset gate helpers

This replaces ad-hoc scattered proof behavior with a first-class controller surface.

## Persisted per-task outcome expectations

Persisted outcomes/checkpoints explicitly include:

- task path
- terminal status
- final acceptance decision
- retry count
- next-task proceed flag
- post-task decision
- accepted-task PR flow flags (created/checks/merged/reset where applicable)

This is the intended truth surface for operator review and deterministic resume behavior.

## Near-term posture

Execution remains intentionally sequential and deterministic.
No concurrent scheduling is introduced.
Acceptance before advance is part of the canonical controller contract, and when autonomous merge posture is enabled, clean-main reset before next-task progression is required.

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`
