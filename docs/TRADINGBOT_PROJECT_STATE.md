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
- Original Task 068 still remains a meaningful follow-on after the stabilization work proves out in practice

## Current state

The orchestrator can now:

- complete ordinary non-protected tasks more reliably than earlier in the project
- enforce explicit deliverable completeness for tasks that name exact required files
- write more truthful failure artifacts for key controller/protected failure paths
- route controller/protected work through narrower, better-defined lanes than before
- persist task-list state and per-task checkpoints for conservative batch progression
- expose a user-facing switch for retaining known-safe runtime artifacts during debugging

However, the project is still **not yet at the point where a backlog/list runner should be considered fully ready**.

The most recent 069–073 work also exposed a remaining gap: internal "green" inside the orchestrator loop does not yet always mean the same thing as the operator’s merge-ready standard under direct local checks and exact branch-diff review.

The next stage must therefore focus on:

- continuing to shrink the controller
- keeping batch/list execution conservative and explicit
- making final autonomous success match operator-observed merge readiness
- only then exposing a first user-facing batch runner CLI and end-to-end proof

## Active continuation order

Immediate near-term order:

- confirm original **068** after the stabilization extension
- then continue the backlog-execution tranche through the merge-readiness hardening follow-ons before the first batch runner CLI

Planned continuation after 073:

- **074a** merge-ready validation profile
- **074b** post-green validation retry loop
- **074c** committed-state parity and unexpected-artifact gate
- **074** batch runner CLI and summary artifacts
- **075** backlog execution end-to-end proof

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`

Any continuation language should reference task IDs exactly as numbered above.


Task 076 adds the next layer on top of that: a dedicated final acceptance reviewer and machine-readable acceptance report that reconcile task-contract requirements, committed/staged diff state, working-tree state, and final validation before the controller declares a task truly finished.

Task 077 builds on 076 by teaching the controller how to classify and self-heal narrow final-acceptance failures with focused repair context instead of broad reruns. This is still conservative: protected/controller breakages are not downgraded into ordinary retryable cleanup.
