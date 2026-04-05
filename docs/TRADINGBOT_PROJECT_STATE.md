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
- accepted-task autonomous PR/check/merge + clean-main reset gate (079)
- explicit resume semantics for post-merge continuation and manual-resolution recovery (080)
- further controller decomposition from `agents/run_task.py` (081)
- first autonomous backlog progression proof over a short ordinary-task manifest (082)

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

## Autonomous backlog proof slice (082)

A narrow, deterministic proof slice is now covered by tests:

- short ordinary manifest progresses task -> acceptance -> merge/reset gate -> next task
- retryable acceptance failure can be self-healed within budget and then accepted without re-running raw execution attempts
- runner stops honestly for non-autonomous outcomes (`manual_patch`, `blocked`, failed merge posture)
- persisted state and summary/outcome artifacts reflect actual run truthfully (no silent continue)

This is intentionally a bounded capability proof, not a broad scheduler claim.

## What 082 still exposed

Task 082 also made the remaining hardening gaps clear:

- controller modules still drift on key decision vocabulary and truth fields
- retry/self-heal semantics need one canonical contract and explicit execution-vs-repair audit fields
- merge/reset posture truth needs to be first-class in persisted state and resume logic
- controller-task failures need a stronger semantic repair digest than raw failing output alone
- controller-core tasks need stricter pre-apply patch quality gates and claim deferral

These are the focus of the next tranche.

## Next controller-contract hardening tranche (083–089)

The next planned tranche focuses on:

- Task 083 first: a new canonical `agents/lib/controller_contract.py` surface used across controller-facing modules
- non-reexecuting retry/self-heal with explicit execution-vs-repair truth fields
- merge-posture truth persistence and resume contract hardening
- semantic failure digest and controller repair-context helpers
- controller-task strict mode and generated-patch quality gate
- further `agents/run_task.py` decomposition through dedicated helper modules
- hardened autonomous short-manifest proof after those contracts are stabilized

## Canonical batch execution path

Canonical path for sequential manifest execution is now:

- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/git_workflow.py`

`agents/run_task.py` remains the execution shell, but it is no longer the sole home of controller behavior.

## Persisted per-task outcome expectations

Persisted outcomes/checkpoints now intentionally aim to include, through one canonical controller contract surface:

- task path
- terminal status
- final acceptance decision
- retry count
- next-task proceed flag
- post-task decision
- accepted-task PR flow flags (created/checks/merged/reset where applicable)
- resume reason/target/gate metadata

The next tranche is intended to make that truth surface canonical and consistent across all controller-facing modules, and to separate raw execution-attempt truth from repair-attempt truth explicitly.

## Near-term posture

Execution remains intentionally sequential and deterministic.
No concurrent scheduling is introduced.
Acceptance before advance is part of the canonical controller contract, and when autonomous merge posture is enabled, clean-main reset before next-task progression is required.

## Scope honesty

Current proof scope is explicitly limited to:

- ordinary/non-protected task manifests
- deterministic local tests and stubs
- conservative stop-on-risk posture

It does **not** claim autonomy for arbitrary protected/controller/meta task lists or unattended broad production scheduling.

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`


## 083 manual-patch posture

Task 083 should still be treated as a manual patch first. It stabilizes the controller contract used by final acceptance, batch execution, batch state persistence, task-queue summaries, merge-posture reporting, and controller-focused tests.

This is a hardening step, not a broader autonomy claim.


- **085** made merge-posture truth first-class persisted checkpoint state and tightened resume contracts to require explicit merged/reset evidence or explicit manual-resolution intent.
