# Orchestrator Controls and Policies

This document describes the stable seams intended for orchestrator integration
tests and monkeypatch-based verification.

## Stable seam registry

The orchestrator shell exposes a registry of supported seam families through:

- `agents.run_task._shell_router_exports()`
- `agents.lib.shell_router.build_shell_seam_registry()`
- `agents.lib.shell_router.shell_seam_exports()`

The registry is intentionally small and stable. It is meant to replace ad hoc
lookups of private globals such as `run_task.some_internal_name`.

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

### Family intent

- `bootstrap`: project scaffold bootstrap helpers
- `spec_mode`: frozen spec artifact and execution-resolution helpers
- `failure_journal`: failure classification, fingerprinting, and journal helpers
- `validator_runner`: validator execution and validator selection helpers
- `artifact_quarantine`: runtime artifact cleanup and classification helpers
- `runtime_foundations`: shell-provider, git, and worktree foundation helpers
- `parser_policy`: file-bundle parsing and protected-file policy helpers
- `semantic_preflight`: semantic inspection and protected API validation helpers
- `shell_router`: outer CLI routing and file-bundle / method-bundle transport helpers

## Intended use in tests

Tests should patch these seams when they need deterministic behavior:

- model / bundle request invocation
- validator invocation
- failure-journal access
- review / quarantine access
- shell routing and bootstrap dispatch

Prefer patching the stable helper returned by the registry rather than reaching
into unrelated internal modules or guessing private names.

## Practical guidance

- Use the registry from `agents.run_task._shell_router_exports()` when a test
  needs the shell-router entrypoint.
- Use `agents.lib.shell_router.shell_seam_exports()` when a test wants the
  canonical seam mapping for all supported families.
- Patch only the helper names listed in the registry for the specific family.
- Avoid monkeypatching unrelated private globals that are not part of the stable
  seam surface.

## Policy notes

- Protected-file method editing remains a separate transport mode.
- Normal file-bundle responses must not include protected method-edit files.
- Tests that mention bundle markers should avoid raw standalone marker lines in
  prose examples; render them inline or split the token if needed.


## Failure classification and remediation planning

The orchestrator should classify failures into distinct categories (for example python syntax, seam-contract mismatch, task-shape mismatch, harness/meta regression, CI-only failure) and choose different remediation paths. The planner should expose an autonomy confidence signal so the controller can decide whether to continue alone, attempt localized repair, patch the task contract, or escalate to the manual patch lane.

## Batch continue gate (explicit post-task decision)

After each queued task, the orchestrator computes and persists one explicit batch
decision:

- `continue`
- `stop`
- `manual_patch`
- `blocked`

The decision is conservative and deterministic. It is grounded in runtime
signals already emitted by the shell and validators, including:

- validator success/failure
- deliverable completeness pass/fail
- protected-lane policy pass/fail
- duplicate bundle conflict artifacts
- manual patch recommendation signals

### Current conservative rules

- Return `continue` only when task status is `completed` and all hard gates pass.
- Return `manual_patch` when the task status is `manual_patch` or when a manual
  patch recommendation is present.
- Return `blocked` for queue-blocking conditions (for example duplicate bundle
  conflict artifacts or explicit blocked status).
- Return `stop` for hard failures that are not blocked/manual-patch.

This prevents silent continuation after hard failures and ensures manual-patch
paths are never auto-advanced.

### Batch-state persistence contract

Batch state persists both:

- `next_task_may_proceed` (boolean gate)
- `post_task_decision` (narrow enum above)

Each task checkpoint also stores the same `post_task_decision`. Resume logic must
treat anything other than `continue` as non-autonomous and require explicit
intervention.

## Duplicate bundle path recovery

When a returned file bundle repeats the same `FILE:` path multiple times, the controller distinguishes between two cases:

- **equivalent duplicates**: every duplicate entry for the path normalizes to the same content
- **conflicting duplicates**: the repeated entries normalize to materially different content

Equivalent duplicates may be collapsed into one accepted file entry when the normalized contents are byte-equivalent after the existing newline normalization rules.

Conflicting duplicates must not be silently resolved by picking one version. Instead, the controller should:

- preserve already accepted non-conflicted files
- run one focused repair request for only the conflicted path(s)
- keep explicit deliverable enforcement active

If the conflicted paths still cannot be resolved after the focused repair attempt, the run writes `last_output_duplicate_bundle_conflict.json` in repo root and fails with a duplicate-conflict error.


## Final acceptance reviewer (076)

The final acceptance reviewer is now the canonical place where the orchestrator reconciles:

- the current task file
- the exact required deliverables parsed from the task contract
- the committed/staged branch diff paths that would become the final result
- the remaining working-tree diff paths
- the authoritative validation profile result
- unexpected tracked artifact findings

It produces one machine-readable acceptance report with a small explicit outcome set:

- `accepted`
- `retryable_failure`
- `manual_patch`
- `blocked`

Conservative rules:

- missing required deliverables at final review reject acceptance
- validation-profile failure is surfaced distinctly from task-contract mismatch
- unexpected tracked artifacts in the final diff block acceptance
- optimistic acceptance is never preferred over explicit rejection

`agents/run_task.py` may still invoke this reviewer, but the reusable policy/report logic should live in a dedicated helper module rather than remain spread across controller flow.
