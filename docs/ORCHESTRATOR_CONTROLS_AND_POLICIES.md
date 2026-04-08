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

## Controller contract posture after 083 planning

Task 083 introduces a canonical `agents/lib/controller_contract.py` surface so controller-facing modules stop restating literal sets independently.

That contract owns at least:

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

Batch state persists both, using the canonical controller contract field names:

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
2. run focused controller proof tests first (`tests/test_controller_contract.py`, `tests/test_run_task_runtime_foundations.py`, `tests/test_task_queue.py`)
3. reject obvious low-discipline bundles before apply when deterministic heuristics can do so safely
4. then require full `ruff check .` and full `pytest -q` before proof-complete claims are accepted
5. defer docs/README proof-complete claims whenever focused controller proof tests are not green
6. avoid over-blocking ordinary non-controller tasks

The current strict-mode pre-apply gate is intentionally heuristic and narrow. It looks for deterministic bad-patch signals in touched controller files such as clustered semicolon statements, compressed multi-imports, suspicious minified formatting, and concentrated unused-import churn.

## Canonical controller contract fields

The controller contract now defines the canonical persisted checkpoint truth fields and resume metadata fields.

Checkpoint truth fields include:

- `post_task_decision`
- `acceptance_decision`
- `retry_count`
- `next_task_may_proceed`
- `accepted_task_pr_flow_completed`
- `required_checks_passed`
- `merged_to_main`
- `clean_main_reset_completed`

Resume metadata fields include:

- `resume_reason`
- `resume_target_task_path`
- `resume_gate`

Merge-posture failures must map through one canonical decision surface:

- `failed_merge`
- `failed_checks`
- `failed_reset`

## Sequential multi-agent loop posture

Task 091 adds the first canonical builder/verifier/controller loop on top of the existing controller surfaces.

Task 092 makes verification authority explicit: local green is not sufficient when the configured profile requires GitHub-required CI checks.

Current conservative posture:

1. controller chooses builder
2. builder produces a machine-readable patch/result bundle
3. controller chooses verifier
4. verifier produces a distinct machine-readable evidence bundle
5. controller remains the only authority that may accept, repair, stop, or advance

Guardrails:

- role execution remains strictly sequential
- verifier evidence must stay distinct from builder output
- passing verifier evidence does not auto-advance by itself
- controller decision remains explicit and machine-readable
- acceptance and merge/reset truth rules from earlier controller tranches remain in force
- task-family routing remains controller-owned; the router may recommend builder, verifier, proof/docs, bootstrap, or constrained/manual lanes, but it may not bypass controller authority

## Hosted CI authority posture

When the configured verification-authority profile requires hosted CI checks, the orchestrator must treat hosted check discovery as first-class evidence.

Current required behavior:

- hosted CI authority absence is itself a blocking signal
- `no checks reported` must not be interpreted as success
- one repo-scoped check contract must be the source of truth for required hosted checks
- persisted batch/checkpoint truth must distinguish hosted probe `unavailable`, `misconfigured`, and `reported_unsatisfied` states
- controller stop posture remains conservative whenever hosted authority is absent or unsatisfied

## Task admission gate

The orchestrator now distinguishes between `autonomous_ordinary`, `supervised_autonomous`, and `manual_only` task-admission lanes. Protected/controller/meta task shapes remain conservative and manual-only. Larger mixed-surface ordinary tasks may still be admissible only under supervision and may require bounded decomposition before execution begins.

## Project-aware validation and authority

Validation and authority must be resolved from the active project contract rather than assuming monorepo defaults. Different projects may carry different focused checks, full checks, bootstrap requirements, and hosted-authority profiles, and the controller must remain truthful when hosted authority is weaker or stronger than local validation evidence.

## Bounded multi-project portfolio scheduler posture (Task 123)

The new portfolio re-proof is intentionally narrow:

- mode: `supervised_local_first`
- bounded slice only across more than one registered project
- per-project isolation for workspace root, branch namespace, state namespace, and carry-forward memory namespace
- next-task selection must remain dependency-truth aware
- authority or merge ineligibility forces conservative stop (`next_task_may_proceed == False`)
- no claim of unattended broad portfolio autonomy


## Public compatibility contract posture (Task 124)

Public/tested compatibility aliases are now frozen through one canonical compatibility contract. Controller/repair code should coerce through that contract for:

- failure helper argument aliases
- project contract convenience keys
- manifest entry path aliases
- manual-patch batch stop status normalization

Future repairs should preserve these spellings rather than reintroducing scattered per-file alias handling.


## Canonical stop vocabulary (Task 126)

Batch status, post-task decision, acceptance decision, and merge-posture failure vocabulary now resolve through one canonical controller-contract mapping layer. Near-synonyms must normalize to the public tested values rather than leaking raw string drift across batch state, batch executor, and merge helpers.
