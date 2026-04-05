# Orchestrator Controls and Policies

This document describes the stable seams intended for orchestrator integration tests and monkeypatch-based verification, plus the current controller-policy posture.

## Stable seam registry

The orchestrator shell exposes a registry of supported seam families through:

- `agents.run_task._shell_router_exports()`
- `agents.lib.shell_router.build_shell_seam_registry()`
- `agents.lib.shell_router.shell_seam_exports()`

The registry is intentionally small and stable. It is meant to replace ad hoc lookups of private globals such as `run_task.some_internal_name`.

## Supported seam families

The current canonical family names are:

- `bootstrap`
- `spec_mode`
- `failure_journal`
- `validator_runner`
- `artifact_quarantine`
- `runtime_foundations`
- `parser_policy`
- `semantic_preflight`
- `shell_router`

Each family maps to the stable helper names that tests may patch or inspect.

## Intended use in tests

Tests should patch these seams when they need deterministic behavior:

- model or bundle request invocation
- validator invocation
- failure-journal access
- review or quarantine access
- shell routing and bootstrap dispatch

Prefer patching the stable helper returned by the registry rather than reaching into unrelated internal modules or guessing private names.

## Controller contract posture after 082

The next hardening tranche should centralize controller truth into one canonical contract surface rather than leaving repeated literal sets spread across modules.

That canonical contract should own at least:

- acceptance decisions
- post-task decisions
- merge-posture terminal decisions
- persisted controller truth-field names
- canonical resume metadata values
- mapping helpers used by batch executor, batch state, final acceptance, task queue, and git workflow

## Batch continue gate (explicit post-task decision)

After each queued task, the orchestrator computes and persists one explicit batch decision.

Current decision surface:

- `continue`
- `stop`
- `manual_patch`
- `blocked`
- `failed_merge`
- `failed_checks`
- `failed_reset`

The decision is conservative and deterministic. It is grounded in runtime signals already emitted by the shell and validators, including:

- validator success or failure
- deliverable completeness pass or fail
- protected-lane policy pass or fail
- duplicate bundle conflict artifacts
- manual patch recommendation signals
- accepted-task merge-posture truth

### Current conservative rules

- Return `continue` only when task status is `completed` and all hard gates pass.
- Return `manual_patch` when the task status is `manual_patch` or when a manual patch recommendation is present.
- Return `blocked` for queue-blocking conditions.
- Return merge-posture failure decisions explicitly when PR, checks, merge, or reset truth says the task cannot safely advance.
- Return `stop` for hard failures that are not blocked or manual-patch.

This prevents silent continuation after hard failures and ensures manual-patch paths are never auto-advanced.

## Batch-state persistence contract

Batch state persists both:

- `next_task_may_proceed` (boolean gate)
- `post_task_decision` (narrow enum above)

Each task checkpoint also stores the same `post_task_decision` plus accepted-task PR flow truth and resume metadata. Resume logic must treat anything other than `continue` as non-autonomous unless canonical persisted resume evidence explicitly proves a safe skip posture.

## Final acceptance reviewer and retry posture

The final acceptance reviewer is the canonical place where the orchestrator reconciles:

- the current task file
- the exact required deliverables parsed from the task contract
- the committed or staged branch diff paths that would become the final result
- the remaining working-tree diff paths
- the authoritative validation profile result
- unexpected tracked artifact findings

It produces one machine-readable acceptance report with a small explicit outcome set:

- `accepted`
- `retryable_failure`
- `manual_patch`
- `blocked`

Retryable self-heal should remain bounded and should be made explicitly non-reexecuting in controller truth: repair the result, rerun validation and acceptance, and do not rerun the raw execution attempt for the same retryable cycle.

## Controller repair guidance posture

Raw failing output should remain available, but controller-core repair should increasingly be driven by a compact semantic digest that names contract drift, merge-posture mismatch, missing persisted truth fields, missing exports, and other controller-family gaps directly.

## Controller-task strict mode posture

Controller-core tasks should run under stricter discipline than ordinary consumer or proof tasks.

At minimum, controller strict mode should:

1. activate for controller-core file shapes
2. run focused controller tests first
3. reject obvious low-discipline bundles before apply when deterministic heuristics can do so safely
4. still require full `ruff check .` and `pytest -q` before proof-complete claims are accepted
5. avoid over-blocking ordinary non-controller tasks
