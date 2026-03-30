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

## Safe Parallelism and Review Contract

The orchestrator supports guarded safe-parallelism planning with review integration, but some planner and review surfaces remain best-effort in the live runtime.

For protected-file review flows, callers should align to the current `run_review()` contract and rely on the presence of:
- `mergeable`
- `reasons`
- `warnings`

Callers and tests should not assume stricter semantics, such as `mergeable == false` or non-empty `reasons` / `warnings`, unless the live implementation explicitly guarantees those outcomes.

## Exact deliverable completeness

When a task enumerates exact files, the controller now treats those paths as part of the live task contract rather than relying only on operator diff review after the run.

At minimum, exact deliverable parsing now recognizes both common backlog section styles:

- `## Deliverables`
- `## Create or update these exact files`

The controller accepts canonical repo-relative required paths under `agents/`, `src/`, `tests/`, `docs/`, and `tasks/`, and it also accepts explicitly named top-level canonical files such as `README.md`. Unsafe or malformed entries such as traversal paths, absolute filesystem paths, or URLs are rejected clearly.

If a task enumerates exact files and one or more of them are missing from the final accepted result, the run is not considered complete. The failure message now identifies both the parsed exact-file contract and which required deliverables were still missing after final lane reconciliation.
