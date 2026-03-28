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


## Manual patch lane bootstrap tasks

The first harness bootstrap tasks in the reliability / recovery / autonomy tranche should not be run through the normal autonomous bundle lane.

Use the manual patch lane for:

- `055a_orchestrator_harness_contract_freeze`
- `055c_orchestrator_seam_manifest_and_semantic_contract_validator`

Resume the autonomous lane with `055b_orchestrator_task_family_classifier_prompt_compiler_and_split_strategy` after 055a is merged.
