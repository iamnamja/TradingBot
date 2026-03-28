# Orchestrator Controls and Policies

## Operating lanes

The orchestrator should explicitly recognize at least four lanes:

1. **docs-only lane**
   - narrative/documentation updates only
   - no engine/meta file edits
2. **narrow tests-only lane**
   - focused unit or compatibility tests
   - deterministic, in-process, no repo-wide recursion
3. **integration-test lane**
   - one integrated scenario across current live seams
   - stricter prompting and semantic validation
4. **protected meta-harness lane**
   - `agents/run_task.py`, `agents/lib/shell_router.py`, protected-file policy, parser/preflight internals
   - protected-method or manual-patch-first workflows only

## Stable harness contract

The following runner-facing surfaces are treated as a stable contract that should not be casually rewritten task-by-task:

- `request_and_parse_bundle(...)`
- `_normalize_policy_path(...)`
- `_task_baseline_paths(...)`
- `enforce_meta_file_task_gate(...)`
- shell-router compatibility with the runner entrypoints and bundle request surface

## Controller intelligence policy

The orchestrator may use model-assisted reasoning internally, but that reasoning must be governed by explicit policies.

The controller-intelligence layer should be responsible for:

- task-family classification
- lane-specific prompt/request compilation
- seam-manifest / semantic contract validation
- failure classification and remediation planning
- autonomy confidence decisions (continue, repair, split, defer, escalate)

The controller-intelligence layer should **not** act as an unconstrained AI supervisor above the orchestrator. It is part of the orchestrator.

## Failure classification policy

When a run fails, the controller should distinguish between at least these classes:

- syntax-only failure
- narrow file-local semantic failure
- task-shape / task-family mismatch
- harness/meta regression
- CI-only failure after generation
- blocked/manual-lane escalation

Each class should map to a different remediation plan rather than forcing the same retry loop every time.

## Localized repair policy

For small task bundles, accepted files should be preserved and only the bad subset should be repaired.

The controller should avoid whole-task restarts when:

- only one file is syntactically invalid
- only one file violates a narrow semantic/preflight rule
- the remaining files are acceptable and deterministic

## Seam-manifest policy

For seam-heavy tasks, the orchestrator should prefer semantic contract validation over brittle substring checks.

Examples:

- validate allowed export keys against a manifest
- allow live helpers like `_failure_journal_exports()`
- block invented alias names like `failure_journal_export`
- distinguish real recursive runner execution from allowed in-process validation seams

## Meta-harness policy

Tasks touching core harness/meta files should not automatically share the same lane as ordinary docs/test tasks.

When a task touches:

- `agents/run_task.py`
- `agents/lib/shell_router.py`
- bundle/preflight/protected-policy internals

it should prefer protected-method mode or a manual patch lane.

## Docs / numbering policy

Task numbering and docs status tables must stay aligned.

When the trajectory changes materially:

- roadmap order must be updated first
- task filenames/headings must reflect the new sequence
- README/task-backlog docs must match the active continuation


## Manual-lane bootstrap rule

For the first reliability / recovery / autonomy tranche, these tasks should **not** go through the normal autonomous generation lane:

- `055a_orchestrator_harness_contract_freeze`
- `055c_orchestrator_seam_manifest_and_semantic_contract_validator`

These are engine self-modification / contract-freeze tasks. They should be landed through a direct manual patch lane first, then the autonomous lane resumes with `055b` and later tasks on top of the frozen contract.
