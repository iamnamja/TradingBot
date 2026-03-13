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
- detect repeated identical bundle failures (>98% similarity triggers escalation)
- escalate repeated failures instead of looping forever
- if agent produces structurally invalid bundle, retry once with format reminder

### Scope discipline
- only task deliverables and explicitly in-scope files may change
- runtime artifacts must be flagged and not block merge when otherwise valid
- out-of-scope changes must block merge unless explicitly allowed by task spec

## Approval policy

Human approval is required for changes to any of:
- runner (`agents/run_task.py`)
- CI/workflow files (`.github/workflows/`)
- dependency files (`requirements.txt`, `pyproject.toml`)
- project adapter or policy modules
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
- no runtime artifact committed

## Failure handling policy

| Failure category | Next action |
|-----------------|-------------|
| `implementation_bug` | retry_task |
| `task_ambiguity` | patch_task_spec |
| `runner_weakness` | patch_runner (requires approval) |
| `ci_dependency_issue` | patch_ci or dependency file (requires approval) |
| `repo_hygiene_issue` | clean_repo |
| `unknown` | require_human_review |

## Runtime artifact policy

Artifacts such as `logs/`, temp/cache files:
- must not block merge by themselves when task is otherwise valid
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
- produce a decision log
- not write to remote branches or GitHub

## Implementation contract policy (mandatory in all task specs)

These patterns must appear as explicit constraints in every orchestrator task spec. They are non-negotiable invariants learned from task 031.

### simulate_backlog contract
```
- call get_next_task([]) directly in the loop — never call scan_tasks() inside the loop
- use continue not break when requires_approval is True
- append task name to processed_tasks BEFORE any break/continue check
```

### run_review contract
```
- empty changed_files → return {"mergeable": True} on legacy/mock path
- never return {"mergeable": False} solely because changed_files is empty
```

### ProjectConfig contract
```
- never @dataclass(frozen=True) on ProjectConfig or any subclass
- always getattr(self.config, "field", default) for optional config fields
```

### Legacy success contract
```
- status == "running"
- message == "Task is now running."
- outcome == "ready_for_pr"
- next_action == "merge"
```

### Failure message contract
```
- message == "Execution failed: {text}" when failure_text or stderr is present
- always read: execution_result.get("failure_text") or execution_result.get("stderr") or ""
```

### Windows compatibility contract
```
- never use echo as subprocess command in tests
- use sys.executable + ["-c", "..."] for cross-platform subprocess calls
- never patch subprocess.run while calling run_next_task() under task_runner_command=None
```

## Task spec quality standards

A task spec is considered high quality when it includes:
- exact method signatures (no new required parameters without explicit justification)
- explicit forbidden patterns list
- exact pseudocode for any algorithmic methods (especially simulate_backlog)
- complete legacy contract table
- Windows compatibility rules
- critical anti-truncation rule (all 5 runner method headers must be present)
- bundle completeness requirement (all deliverables listed)
- material update definition
