# Orchestrator Vision and Controls

## Task-family aware prompting

The orchestrator classifies tasks into lightweight families before compiling the LLM request:

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

## Task-scope heuristics and split recommendations

The orchestrator also applies lightweight task-scope heuristics before compiling the final request. The goal is to recognize when a task is likely broader than a single safe request and should be narrowed or split into focused follow-on work.

These heuristics are advisory. They do **not** require mandatory auto-splitting and they do **not** prevent execution on their own. Instead, they let the harness warn, annotate, and recommend smaller follow-on tasks when the requested scope appears too wide.

A split recommendation is most likely to appear when a task mixes multiple seam families that have historically produced broad or fragile edits, including combinations across:

- **bootstrap/config surfaces**
- **failure-journal/reporting seams**
- **safe-parallelism/review semantics**
- **runtime artifact quarantine behavior**
- **broad docs normalization**

The heuristics are intentionally lightweight and should stay compatible with evolving controller behavior. The purpose is to surface likely risk, not to encode brittle or overly opinionated rules.

## Broad multi-seam examples

A task may be marked as split-recommended when it appears to combine more than one high-risk seam family in a single request. Representative examples include:

- a protected meta-harness/controller change that also asks for broad runtime-reporting or failure-journal behavior changes
- a task that combines safe-parallelism or review-contract semantics with artifact quarantine and controller routing changes
- a task that asks for both substantial bootstrap/config reshaping and broad documentation normalization in one pass
- a task that mixes integration/e2e expectations with protected meta-harness changes in a way that is likely to force wide edits

When this happens, the orchestrator can include an explicit split recommendation in the compiled request so the work can be broken into smaller, safer tasks.

## Why this matters

Task-family classification, lane-specific request shaping, and split recommendations help the orchestrator:

- keep scope tighter,
- reduce broad rewrites,
- improve protected-file policy adherence,
- and converge more deterministically on `ruff` + `pytest`.

This is especially important for controller and protected-lane work, where apparently related changes often span multiple seams and are more reliable when split into narrower continuations.

## Safe Parallelism and Review Contract

The orchestrator supports guarded safe-parallelism planning with review integration, but some planner and review surfaces remain best-effort in the live runtime.

For protected-file review flows, callers should align to the current `run_review()` contract and rely on the presence of:
- `mergeable`
- `reasons`
- `warnings`

Callers and tests should not assume stricter semantics, such as `mergeable == false` or non-empty `reasons` / `warnings`, unless the live implementation explicitly guarantees those outcomes.
