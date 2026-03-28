# Orchestrator Vision and Controls

## Task-family aware prompting

The orchestrator now classifies tasks into lightweight families before compiling the LLM request:

- **docs-only**: all required paths are documentation artifacts.
- **narrow tests-only**: only `tests/` paths are required.
- **integration-test**: task text or required paths indicate integration/e2e coverage.
- **protected meta-harness**: task touches protected harness/meta seams (for example `agents/run_task.py`, `agents/lib/shell_router.py`, `agents/lib/bundle_parser.py`, `agents/lib/protected_file_policy.py`).

This classification is intentionally heuristic and deterministic. It is used to pick a lane and shape the request, not to hard-block execution.

## Lane-specific prompt compilation

Instead of one generic request shape, the orchestrator compiles a lane-specific request section:

- **docs-only lane**: constrains edits to docs and discourages runtime churn.
- **narrow tests-only lane**: emphasizes targeted test fixes and minimal implementation support.
- **integration-test lane**: emphasizes end-to-end wiring, deterministic fixtures, and realistic boundaries.
- **protected meta-harness lane**: emphasizes strict policy compliance and minimal safe patches.

Lane-aware prompt compilation improves reliability by reducing ambiguous guidance and matching instructions to seam risk.

## Split strategy for multi-seam risk

The classifier can emit a split recommendation when a task mixes risky seam families.  
A key example is a task that combines **integration-test** + **protected meta-harness** concerns; this is flagged as split-recommended because it tends to produce broad, fragile edits.

When split is recommended, the orchestrator includes an explicit warning in the compiled request so work can be broken into smaller, safer tasks.

## Why this matters

Task-family classification + lane-specific request shaping + split recommendations provide:

- better scope control,
- fewer broad rewrites,
- better protected-file policy adherence,
- and more deterministic convergence on `ruff` + `pytest`.
