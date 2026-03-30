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
- start decomposing `agents/run_task.py` into extracted helper modules

However, the project is still **not yet at the point where a backlog/list runner should be considered fully ready**.

The next stage must focus on:

- continuing to shrink the controller
- representing task lists explicitly
- persisting batch state and resume behavior
- adding safe per-task isolation and post-task continue/stop policy
- only then exposing a user-facing batch runner

## Active continuation order

Immediate near-term order:

- confirm original **068** after the stabilization extension
- then begin the backlog-execution continuation at **069**

Planned continuation after 068:

- **069** controller decomposition second extraction
- **070** task-list manifest and queue model
- **071** batch state persistence and resume
- **072** per-task checkpoint and branch isolation
- **073** batch failure policy and continue gate
- **074** batch runner CLI and summary artifacts
- **075** backlog execution end-to-end proof

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md`
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`

Any continuation language should reference task IDs exactly as numbered above.
