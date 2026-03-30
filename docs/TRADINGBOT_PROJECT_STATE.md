# TradingBot Project State

## Repository scope

The repository combines:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through the reliability/autonomy continuation and its immediate follow-ons with the following sequence complete:

- Core orchestrator lifecycle and workflow execution (015–038 family)
- Harness hardening and modularization (039–043)
- Spec execution and reliability lanes (044–048)
- Shell convergence and interface stabilization (049–050)
- Docs/status normalization and seam preparation (051–054 + 054a/054b)
- Reliability/autonomy umbrella and implementations (055–060)
- Continuation reset and resumed follow-ons (061–067 + 065a + 067a)

## Current state

The orchestrator can now:

- complete ordinary non-protected tasks more reliably than before
- enforce explicit deliverable completeness for tasks that name exact required files
- write truthful failure artifacts for key protected/controller failure paths

However, post-067 execution also showed that the system is **not yet at the point where protected/controller-file tasks can be trusted to complete autonomously**.

The next work is therefore a stabilization extension focused on:

- real protected execution lane behavior
- duplicate-bundle recovery
- making `agents/run_task.py` less monolithic

## Active continuation order

The next task sequence is:

- **068a** protected lane execution hardening
- **068b** duplicate bundle normalization and focused repair
- **068c** controller decomposition and first extraction
- **068** task scope / split heuristics (resume after the stabilization extension)

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md` (source of truth for task order and status labels)
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`

Any continuation language should reference task IDs exactly as numbered above (no alternate renumbering aliases).
