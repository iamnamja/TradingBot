# TradingBot Project State

## Repository scope

The repository combines:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through the reliability/autonomy continuation and its immediate stabilization extension with the following sequence complete or in progress:

- Core orchestrator lifecycle and workflow execution (015–038 family)
- Harness hardening and modularization (039–043)
- Spec execution and reliability lanes (044–048)
- Shell convergence and interface stabilization (049–050)
- Docs/status normalization and seam preparation (051–054 + 054a/054b)
- Reliability/autonomy umbrella and implementations (055–067 + 065a + 067a)
- Stabilization extension to support protected/controller execution and controller thinning (068a–068c)
- 068–075: backlog execution continuation, merge-readiness hardening, first conservative batch runner, and first narrow end-to-end backlog proof

## Current state

The orchestrator can now:

- complete ordinary non-protected tasks more reliably than earlier in the project
- enforce explicit deliverable completeness for tasks that name exact required files
- write more truthful failure artifacts for key controller/protected failure paths
- route controller/protected work through narrower, better-defined lanes than before
- persist task-list state and per-task checkpoints for conservative batch progression
- expose a user-facing switch for retaining known-safe runtime artifacts during debugging
- run a short backlog manifest end-to-end under deterministic local tests
- stop conservatively on manual-patch or blocked outcomes rather than auto-advancing
- enforce continue-gate behavior so hard failures do not silently progress to later tasks
- expose a first conservative batch runner CLI with machine/human summary artifacts
- require an authoritative merge-ready validation profile and committed-state parity before final autonomous success

Task 075 provides the first narrow end-to-end proof that sequential backlog execution works with persisted batch state and summary accounting, while remaining intentionally conservative for protected/controller paths.

This remains a proof slice, not a broad production scheduler.

## What is still not done

The orchestrator is still **not yet at the point where an arbitrary list of tasks should be fed in unattended and expected to run/repair/merge continuously on its own**.

The key remaining gaps are:

- final acceptance review still needs a dedicated reusable surface
- retryable acceptance failures still need targeted self-heal logic
- accepted-task PR/check/merge/reset lifecycle is not yet a first-class autonomous controller surface
- resume-after-merge and resume-after-manual-resolution are not yet explicit enough
- `agents/run_task.py` still owns too much orchestration flow

## What “ready for a list” means

The next milestone is not “arbitrary broad scheduler.”  
The next honest milestone is:

- short ordinary-task manifest
- retryable self-heal inside bounded limits
- final acceptance review after all tests
- accepted-task PR/check/merge/reset before next-task continuation
- explicit stop on manual/blocked/merge-failure conditions

That is the target of 076–082.

## Active continuation order

Immediate near-term order:

- maintain original 068 confirmation as historical prerequisite
- continue into the autonomy-and-controller-thinning tranche after the 075 proof slice

Planned continuation after 075:

- **076** final acceptance reviewer and report
- **077** targeted self-heal for acceptance failures
- **078** batch executor loop and acceptance controller
- **079** autonomous PR/merge and main-reset gate
- **080** batch resume after merge and manual resolution
- **081** controller decomposition third extraction
- **082** autonomous backlog runner proof

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`

Any continuation language should reference task IDs exactly as numbered above.
