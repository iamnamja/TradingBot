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

- **Tasks 090–099 proof sync complete:** the repo now has synchronized deterministic proof for a canonical three-role multi-agent contract surface (`controller`, `builder`, `verifier`), dependency-aware short-manifest planning, explicit verification-authority truth, Python-only second-project portability, and extraction-prep boundary posture.

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

The workspace adapter contract keeps TradingBot as one consumer rather than the only implied consumer, and gives the controller explicit bootstrap truth (`not_started`, `succeeded`, `blocked`) so resume behavior can remain honest after setup failures in external Python workspaces.

## Standalone package boundary and consumer bridge (098–099)

The orchestrator has a clearer standalone product boundary without claiming full extraction completion.

This boundary is expressed through:

- explicit reusable contract surfaces for multi-agent role and workspace consumer bridges
- a documented minimal consumer bridge for workspace adapters, validation commands, acceptance evidence hooks, protected paths, and optional consumer policies
- TradingBot remaining a supported in-repo consumer while generic Python remains a second consumer shape

The repo still operates as a monorepo, and posture remains extraction-prep only.

## Second-project portability proof (097–099)

A narrow deterministic proof covers a simple external Python project shape and demonstrates:

- workspace adapter selection between TradingBot and generic Python consumers
- explicit bootstrap/setup truth and resumable failure signaling
- builder/verifier/controller role separation in a sequential controller-owned loop
- dependency-aware short-manifest progression over two ordered tasks
- truthful continue/stop posture based on verifier authority and controller final decision

Scope remains intentionally Python-first and local-test deterministic.

## Scope honesty

Current proof scope is explicitly limited to:

- role-separated controller/builder/verifier contracts in sequential execution
- dependency-aware short-manifest planning/routing truth
- explicit verification-authority posture (`local_only` and required-check truth surfaces)
- deterministic local tests and stubs
- simple external Python project/workspace shapes through the adapter contract
- extraction preparation posture rather than completed standalone extraction

It does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.
