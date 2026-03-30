# TradingBot Project State

## Repository scope

The repository combines:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Implemented baseline

The orchestrator buildout has progressed through the reliability/autonomy tranche with the following sequence complete:

- Core orchestrator lifecycle and workflow execution (015–038 family)
- Harness hardening and modularization (039–043)
- Spec execution and reliability lanes (044–048)
- Shell convergence and interface stabilization (049–050)
- Docs/status normalization and seam preparation (051–054 + 054a/054b)
- Reliability/autonomy umbrella and implementations (055–060)

## Continuation reset (this sync point)

To prevent post-tranche drift, continuation is explicitly resumed from:

- **061** `orchestrator_continuation_reset_and_numbering_sync` (this alignment task)

Follow-on deferred continuation remains:

- **062** integrated capabilities e2e
- **063** failure journal live seam
- **064** safe parallelism review integration
- **065** runtime artifact quarantine integration
- **066** package extraction prep
- **067** canonical docs path policy
- **068** task scope and split heuristics

## Canonical ordering source

For all contributor and automation references, the canonical visible order is:

1. `tasks/README.md` (source of truth for task order and status labels)
2. task markdown files under `tasks/` by exact numeric/alphanumeric filename
3. supporting roadmap docs in `docs/`

Any continuation language should reference task IDs exactly as numbered above (no alternate renumbering aliases).
