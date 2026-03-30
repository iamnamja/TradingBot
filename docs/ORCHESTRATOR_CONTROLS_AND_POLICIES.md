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

## Deliverable completeness enforcement

When a task includes an explicit deliverable file list under a supported heading
such as `Create or update these exact files`, `Deliverables`, `Files`, or
`Required files`, the runner treats that list as a conservative completeness
contract.

In that mode:

- validator-green is not sufficient on its own
- every explicitly listed deliverable must be present in the final accepted file set
- the controller may attempt one focused missing-file repair that asks only for
  the missing deliverables while preserving already accepted files
- unresolved missing deliverables produce a durable
  `last_output_deliverable_completeness_failure.json` artifact in repo root

No deliverable completeness enforcement is applied when the task text is
ambiguous or does not include one of the supported explicit file-list sections.

