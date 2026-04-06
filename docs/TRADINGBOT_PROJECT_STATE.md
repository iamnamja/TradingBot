# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through reliability/autonomy continuation, conservative batch execution hardening, controller-contract hardening, and proof synchronization.

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
- canonical controller contract, non-reexecuting retry/self-heal truth, merge-posture truth persistence, controller semantic repair context, strict-mode gating, and a fourth controller extraction (083–088)
- hardened short-manifest proof synchronization (089)

## Current state


- **Tasks 090–094 foundation complete:** the repo now has a canonical three-role multi-agent contract surface (`controller`, `builder`, `verifier`), persisted role handoff truth, a sequential builder/verifier/controller loop with distinct machine-readable role artifacts and controller-owned final authority, explicit verification-authority truth for GitHub-required CI checks, and a reusable Python-first project/workspace adapter contract for bootstrap and validation outside the current repo shape.

The orchestrator now has an explicit per-task sequential controller loop that:

1. runs task execution
2. runs authoritative validation
3. runs final acceptance review
4. retries self-heal only when acceptance is retryable and budget remains, without raw re-execution for the same attempt
5. persists explicit terminal task outcome details and merge/reset truth
6. for accepted tasks, can optionally run PR/create/check/merge and enforce clean-main reset before next task
7. advances or stops conservatively

Conservative stop behavior is explicit and tested:

- `manual_patch` stops the loop
- `blocked` stops the loop
- PR/CI/merge/reset failure in autonomous merge posture stops honestly and prevents advancement

Accepted tasks continue only when all enabled gates pass.

The new workspace adapter contract keeps TradingBot as one consumer rather than the only implied consumer, and gives the controller explicit bootstrap truth (`not_started`, `succeeded`, `blocked`) so resume behavior can remain honest after setup failures in external Python workspaces.

## Hardened autonomous short-manifest proof (089)

A narrow, deterministic proof slice is now covered and synchronized across tests/docs.

The current proof demonstrates:

- short ordinary manifest progresses through task execution, authoritative validation, and final acceptance review
- retryable acceptance failure can be self-healed within budget and then accepted without re-running raw execution attempts
- accepted tasks can pass the PR/check/merge/reset gate before the next task proceeds
- runner stops honestly for failed merge/check/reset posture
- resume-after-merge only skips prior tasks when persisted checkpoint truth proves accepted + checks passed + merged + clean reset
- controller-core proof-shaping tasks defer docs/README proof-complete claims until focused controller proof tests are green

This remains an intentionally bounded capability proof, not a broad scheduler claim.

## What 083–089 hardened

The controller-contract hardening tranche stabilized:

- one canonical controller contract across controller-facing modules
- non-reexecuting retry/self-heal semantics with explicit repair-vs-execution audit truth in the proof surface
- first-class merge/reset posture truth in persisted state and resume logic
- controller-task semantic repair digest/context rather than raw failing logs alone
- controller strict mode, focused proof tests, and proof-claim deferral for docs/README
- further `agents/run_task.py` decomposition through dedicated helper modules

## Next planned tranche (090–099)

The next tranche should shift from controller-contract hardening to multi-agent portability and productization.

Planned focus areas are:

- canonical builder/verifier/controller role contract and handoff truth
- sequential multi-agent execution loop with controller-owned role selection and distinct builder/verifier/controller evidence bundles
- CI-required checks as first-class verification authority with explicit missing/pending/timed-out/failed/pass truth
- repair-strategy routing instead of one generic remediation surface
- reusable project/workspace bootstrap and validation contracts
- dependency-aware manifests and task-family routing
- a second-project Python portability proof
- a stronger standalone product boundary while still remaining in the monorepo for this tranche

## Canonical batch execution path

Canonical path for sequential manifest execution is now:

- `agents/lib/batch_executor.py`
- `agents/lib/batch_state.py`
- `agents/lib/task_queue.py`
- `agents/lib/final_acceptance.py`
- `agents/lib/git_workflow.py`

`agents/run_task.py` remains the execution shell, but it is no longer the sole home of controller behavior.

## Persisted per-task outcome expectations

Persisted outcomes/checkpoints now intentionally include, through one canonical controller contract surface:

- task path
- terminal status
- final acceptance decision
- retry count
- next-task proceed flag
- post-task decision
- accepted-task PR flow flags (created/checks/merged/reset where applicable)
- resume reason/target/gate metadata

## Near-term posture

Execution remains intentionally sequential and deterministic.
No concurrent scheduling is introduced.
Acceptance before advance is part of the canonical controller contract, and when autonomous merge posture is enabled, clean-main reset before next-task progression is required.

The next broadened product step should still keep role execution sequential at first:

- controller chooses
- builder acts
- verifier acts
- controller decides

## Scope honesty

Current proof scope is explicitly limited to:

- ordinary/non-protected task manifests
- deterministic local tests and stubs
- conservative stop-on-risk posture
- controller-core proof-shaping tasks governed by strict-mode proof gates

It does **not** claim autonomy for arbitrary protected/controller/meta task lists or unattended broad production scheduling.

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`
