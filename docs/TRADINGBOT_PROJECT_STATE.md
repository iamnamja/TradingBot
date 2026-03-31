# TradingBot Project State

## Repository scope

The repository combines:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through the reliability/autonomy continuation and the backlog-execution preparation tranche with the following sequence complete or in progress:

- Core orchestrator lifecycle and workflow execution (015–038 family)
- Harness hardening and modularization (039–043)
- Spec execution and reliability lanes (044–048)
- Shell convergence and interface stabilization (049–050)
- Docs/status normalization and seam preparation (051–054 + 054a/054b)
- Reliability/autonomy umbrella and implementations (055–067 + 065a + 067a)
- Stabilization extension to support protected/controller execution and controller thinning (068a–068c)
- Original Task 068 confirmation after the stabilization extension
- 069 controller decomposition second extraction
- 070 task-list manifest and queue model
- 070a exact-deliverable parser and completion gate hardening
- 070b runtime artifact retention and visibility
- 071 batch state persistence and resume

## Current state

The orchestrator can now:

- complete ordinary non-protected tasks more reliably than earlier in the project
- enforce explicit deliverable completeness for tasks that name exact required files using the current task contract styles
- represent a deterministic task queue and persist machine-readable batch execution state
- resume backlog execution from saved state
- quarantine known-safe runtime artifacts by default on successful pushed runs while supporting internal retention logic
- continue decomposing `agents/run_task.py` into extracted helper modules

However, one follow-up remains before moving deeper into backlog execution policy:

- the runtime-artifact retention capability is not yet surfaced cleanly to operators through an explicit CLI/env switch

## Active continuation order

Immediate near-term order:

- **071a** user-facing runtime artifact retention switch
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
