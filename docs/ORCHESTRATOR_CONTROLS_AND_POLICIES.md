# Orchestrator Controls and Policies

## Overview
This document formalizes the controls that govern orchestrator behavior.

## Core controls
### Repo discipline
- require a clean worktree before starting
- always create a dedicated branch per task
- never commit directly to `main`
- sync `main` before starting a new task

### Retry discipline
- cap retries
- detect repeated identical failures
- escalate repeated failures instead of looping forever

### Scope discipline
- only task deliverables and allowed in-scope files may change
- runtime artifacts must be flagged
- out-of-scope changes must block merge unless explicitly allowed

## Approval policy
Human approval is required for:
- runner changes
- workflow / CI changes
- dependency file changes
- project adapter / policy changes
- secrets or auth-related changes
- live-trading related changes
- protected file modifications
- repair actions classified as high risk

## Merge policy
A PR may be auto-merged only when:
- review checker says mergeable
- CI passes
- no approval is required
- no protected-file violation exists

## Failure handling policy
Failure categories should map to next actions:
- implementation_bug -> retry_task
- task_ambiguity -> patch_task
- runner_weakness -> patch_runner (approval)
- ci_dependency_issue -> patch_ci or dependency file (approval)
- repo_hygiene_issue -> clean_repo
- unknown -> require_human_review

## Runtime artifact policy
Artifacts such as:
- `logs/`
- temp/cache files
must:
- not block merge by themselves when otherwise in scope
- be cleaned or ignored before final merge
- appear in warnings/audit trail

## Resume/recovery policy
The orchestrator must:
- persist state after each major step
- detect interrupted runs
- recover without losing task state
- avoid double-merging or double-running the same successful task

## Dry-run policy
Dry-run mode must:
- simulate actions without mutating repo/PR state
- show what would be done
- produce a decision log
- not write to remote branches or GitHub
