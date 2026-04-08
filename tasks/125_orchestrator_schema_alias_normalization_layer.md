# Task 125 — Orchestrator schema alias normalization layer

## Goal
Centralize alias normalization for task manifests, project contracts, and repair/remediation payloads.

## Scope
- `task` / `path` / `task_path`
- `workspace_root` / `project_workspace_root`
- `kind` / `failure_kind`
- `message` / `failure_message`
- `category` / `failure_category`

## Required changes
- add a canonical normalization layer used by all consumer modules
- remove duplicated ad hoc alias logic where possible
- keep behavior deterministic and serializable

## Acceptance
- focused tests prove normalized equivalence
- task queue, registry, and failure journal consume the shared normalizer
- full `ruff check .` and `pytest -q` are green
