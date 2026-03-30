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

## Protected method mode routing and truthful failure artifacts

When a task explicitly lists protected meta harness files such as `agents/run_task.py` or `agents/lib/shell_router.py` in its required deliverables, those files must be pre-routed out of the normal file-bundle lane. Ordinary non-protected deliverables in the same task may still remain eligible for the normal bundle lane.

The runtime must not claim that `_last_agent_model_output.txt` or `_last_agent_file_bundle.txt` were saved unless those files actually exist on disk. If a protected-file failure occurs before any model output or parsed file bundle exists, the runtime should write truthful placeholder artifacts that explain what failed, whether a normal bundle was attempted, and which protected files were involved.



## Protected execution lane

When a task explicitly requires protected meta harness files such as `agents/run_task.py` or `agents/lib/shell_router.py`, the controller should not send those files through the ordinary file-bundle lane.

The protected execution lane is intentionally narrow:

- protected deliverables are partitioned out of the normal bundle scope
- known protected controller files may be assigned a deterministic protected target profile
- mixed tasks may still keep non-protected deliverables in the normal bundle lane
- final deliverable accounting must reconcile accepted files from both lanes before validators run

If protected execution fails after routing, the runtime must still emit truthful failure artifacts describing whether protected execution was attempted, whether the task was mixed protected/non-protected, and which protected targets were identified.
