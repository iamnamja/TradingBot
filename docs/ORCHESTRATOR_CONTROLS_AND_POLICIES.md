# Orchestrator Controls and Policies

## Overview

This document formalizes the controls that govern orchestrator behavior. These policies apply to all tasks from 032 onward.

## Core controls

### Repo discipline

- require a clean worktree before starting any task
- always create a dedicated branch per task (`agent-{task-stem}`)
- never commit directly to `main`
- sync `main` before starting a new task (`git fetch origin && git reset --hard origin/main && git clean -fd`)

### Retry discipline

- cap retries at 4 iterations per task run
- detect repeated identical bundle failures
- escalate repeated failures instead of looping forever
- if the agent produces a structurally invalid bundle, retry once with a format reminder

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

## Merge policy

A PR may be auto-merged only when ALL of:

- review checker says `mergeable: True`
- CI passes
- `requires_approval == False`
- no protected-file violation exists
- no runtime artifact is committed
- task-policy compliance is satisfied

## Failure handling policy

| Failure category | Next action |
|-----------------|-------------|
| `implementation_bug` | retry_task |
| `task_ambiguity` | patch_task_spec |
| `runner_weakness` | patch_runner (requires approval) |
| `ci_dependency_issue` | patch_ci or dependency file (requires approval) |
| `repo_hygiene_issue` | clean_repo |
| `policy_violation` | reject_bundle |
| `unknown` | require_human_review |

## Runtime artifact policy

Artifacts such as `logs/`, temp/cache files:

- must not block merge by themselves when the task is otherwise valid
- must be cleaned or `.gitignore`'d before final merge
- must appear in warnings/audit trail

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

## Protected-file policy

Task specs should use one of these explicit modes when needed:

### exact-copy-plus-append-method

Use when a file such as `runner.py` is included only to add one method.

Requirements:

- copy the file exactly
- add only the named method
- do not change existing methods, imports, strings, or contracts

### method-add-only

Use when one small helper or branch is being added to an otherwise locked file.

### tests-only

Use when production behavior is already correct and only coverage is needed.

### config-only

Use when work must stay within adapters/config/schema files.

### docs-only

Use when only markdown or text documentation may change.

Bundles that violate the declared mode must be rejected even if tests pass.

## Implementation contract policy (mandatory in all task specs)

These patterns must appear as explicit constraints in every orchestrator task spec.

### simulate_backlog contract

- call `get_next_task([])` directly in the loop — never call `scan_tasks()` inside the loop
- use `continue` not `break` when `requires_approval` is `True`
- append task name to `processed_tasks` BEFORE any break/continue check

### run_review contract

- empty `changed_files` → return `{"mergeable": True}` on legacy/mock path
- never return `{"mergeable": False}` solely because `changed_files` is empty

### ProjectConfig contract

- never `@dataclass(frozen=True)` on `ProjectConfig` or any subclass
- always `getattr(self.config, "field", default)` for optional config fields

### Legacy success contract

- `status == "running"`
- `message == "Task is now running."`
- `outcome == "ready_for_pr"`
- `next_action == "merge"`

### Failure message contract

- `message == "Execution failed: {text}"` when failure_text or stderr is present
- always read: `execution_result.get("failure_text") or execution_result.get("stderr") or ""`

### Windows compatibility contract

- never use `echo` as subprocess command in tests
- use `sys.executable + ["-c", "..."]` for cross-platform subprocess calls
- never patch `subprocess.run` while calling `run_next_task()` under `task_runner_command=None`

## Task spec quality standards

A task spec is considered high quality when it includes:

- exact method signatures
- explicit forbidden patterns list
- exact pseudocode for algorithmic methods where needed
- complete legacy contract table
- Windows compatibility rules
- protected-file mode or tests-only/config-only rule where applicable
- bundle completeness requirement
- material update definition
- a task scope that is small enough to avoid high-risk multi-file rewrites
