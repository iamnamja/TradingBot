# Orchestrator Controls and Policies

## Overview

This document formalizes the controls that govern orchestrator behavior.

Tasks 032–048 are now complete in substance. The next tranche (049–054) focuses on shell convergence, public interface freeze, docs/status normalization, portability proof, integrated end-to-end scenarios, and package extraction prep.

## Core controls

### Repo discipline

- require a clean worktree before starting any task
- always create a dedicated branch per task (`agent-{task-stem}` or explicit fix branch)
- never commit directly to `main`
- sync `main` before starting a new task (`git fetch origin && git reset --hard origin/main && git clean -fd`)
- distinguish clearly between task-shape failures, shell/harness failures, and true product/code failures

### Retry discipline

- cap retries at 4 iterations per task run
- detect repeated identical bundle failures
- escalate repeated failures instead of looping forever
- if the agent produces a structurally invalid bundle, retry once with a format reminder
- preserve a bounded raw failure snippet for the next retry when useful
- prefer direct curated patches when repeated retries keep corrupting protected or high-leverage shell surfaces

### Scope discipline

- only task deliverables and explicitly in-scope files may change
- runtime artifacts must be flagged and not block merge when otherwise valid
- out-of-scope changes must block merge unless explicitly allowed by task spec
- green tests do not override task policy or protected-file restrictions

## Approval policy

Human approval is required for changes to any of:

- runner (`agents/run_task.py`)
- CI/workflow files (`.github/workflows/`)
- dependency files (`requirements.txt`, `pyproject.toml`)
- project adapter or policy modules when the task did not explicitly call for them
- secrets or auth-related files
- live-trading related code paths
- protected file patterns (defined per project config)
- repair actions classified as high risk
- orchestrator packaging / extraction surfaces

## Merge policy

A PR may be auto-merged only when ALL of:

- review checker says `mergeable: True`
- CI passes
- `requires_approval == False`
- no protected-file violation exists
- no non-recoverable runtime artifact is committed
- task-policy compliance is satisfied

## Failure handling policy

| Failure category | Next action |
|-----------------|-------------|
| `implementation_bug` | retry_task |
| `task_ambiguity` | patch_task_spec or route to spec mode |
| `runner_weakness` | patch_runner (requires approval) |
| `ci_dependency_issue` | patch_ci or dependency file (requires approval) |
| `repo_hygiene_issue` | clean_repo |
| `policy_violation` | reject_bundle |
| `unknown` | require_human_review |

## Runtime artifact policy

Artifacts such as `logs/`, temp/cache files, and runner-generated local artifacts:

- must not block merge by themselves when the task is otherwise valid
- should be auto-quarantined when they match the known safe list
- must be cleaned or `.gitignore`'d before final merge
- must appear in warnings/audit trail
- must fail the task only when the artifact is unknown, unrecoverable, or outside the safe list

Known safe artifacts for quarantine should include runner-local files such as:

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`
- other explicitly declared local audit/debug artifacts

## Resume/recovery policy

The orchestrator must:

- persist state after each major step
- detect interrupted runs
- recover without losing task state
- avoid double-merging or double-running the same successful task

## Dry-run policy

Dry-run mode must:

- simulate actions without mutating repo or PR state
- show what would be done
- produce a decision log when the task explicitly calls for it
- not write to remote branches or GitHub

## Spec / execution policy

The orchestrator should support two distinct modes:

### Spec mode

Used when the task is still ambiguous.

Responsibilities:
- clarify scope
- identify edge cases
- identify forbidden patterns
- define acceptance criteria
- define verification commands and expected outputs
- freeze the task into an execution-ready spec artifact

### Execution mode

Used only after the spec is frozen.

Responsibilities:
- consume the frozen task artifact
- implement the requested work
- run validators/checks
- retry within normal policy bounds
- avoid changing scope unless escalated

## Protected-file policy

Task specs should use one of these explicit modes when needed:

### exact-copy-plus-append-method

Use when a protected file is included only to add one helper/export seam.

### exact-copy-plus-replace-method

Use when a protected Python file must keep exact-copy discipline outside one existing method replacement.

### method-add-only

Use when one small helper or branch is being added to an otherwise locked file.

### tests-only

Use when production behavior is already correct and only coverage is needed.

### config-only

Use when work must stay within adapters/config/schema files.

### docs-only

Use when only markdown or text documentation may change.

Bundles that violate the declared mode must be rejected even if tests pass.

## Thin-shell convergence policy

The public shell `agents/run_task.py` should converge toward:

- one stable definition per exported wrapper/helper
- no duplicate export-seam definitions
- no duplicate compatibility wrapper definitions
- minimal inline business logic once a reusable helper module exists
- preserved public behavior for the rest of the repo and tests

When the shell is touched, tasks must prefer **behavior-preserving convergence** over adding new shell logic.

## Machine-readable task contract directives

Task specs may include machine-readable contract directives so the harness can enforce semantics earlier.

Examples:

- `CONSTRUCTOR: module.Class(arg1, arg2, arg3)`
- `CONFIG_WRAPPER: module.Class first_arg_requires=.config unless=ProjectConfig`
- `ALLOWED_METHODS: module.Class run_next_task run_loop`
- `FORBID_IMPORTS: module symbol1 symbol2`
- `FORBID_CALLS: runner.run runner.run_all_tasks`
- `RESULT_KEYS: run_loop processed_tasks stopped_reason final_status approval_required planned_actions`
- `VERIFY_COMMANDS: ruff check . ; pytest -q`
- `VERIFY_EXPECTS: cli_command output_contains="..."`

These directives are additive and do not replace normal prose.

## Validator plugin policy

Projects may define additional validators beyond `ruff` and `pytest`, such as:

- CLI smoke checks
- snapshot checks
- schema validators
- API contract validators
- UI screenshot or render validators

These validators should be configured in project adapters/config, not hardcoded in the core engine.

Legacy runtime-foundations wrapper behavior must remain compatible for the built-in `ruff` / `pytest` path unless intentionally changed in a dedicated task.

## Safe parallelism policy

Parallel task execution is allowed only when tasks are explicitly marked independent.

Parallel mode must:
- never operate on overlapping protected files
- never operate on shared mutable state without isolation
- never bypass approval policy
- require deterministic fan-in / merge ordering
- default to off unless the task class is explicitly parallel-safe

## Portability proof policy

Before packaging or repo extraction, the orchestrator must demonstrate:

- a second non-TradingBot project adapter/config path
- bootstrap outputs that are generic rather than TradingBot-specific
- validator selection through adapter/config rather than shell hardcoding
- end-to-end scenarios that combine runtime artifacts, spec mode, failure journaling, validators, and safe parallelism
