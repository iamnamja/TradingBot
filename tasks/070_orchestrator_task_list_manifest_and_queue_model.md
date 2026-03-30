# Task 070 — Orchestrator task-list manifest and queue model

## Why this task exists

The long-term goal is for the orchestrator to take a list of tasks and work through them automatically.

Before it can execute a backlog, it needs a stable, machine-readable way to represent a task list, validate that list, and decide what is queued versus blocked.

## Outcome

Add a narrow task-list manifest format and queue model that can represent a backlog of task files without yet attempting a full autonomous batch runner.

## Create or update these exact files

- `agents/run_task.py`
- `agents/lib/task_queue.py`
- `tests/test_run_task_runtime_foundations.py`
- `tests/test_task_queue.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Task-list manifest support

Introduce a small manifest format that can describe a list of task files, for example:

- plain ordered task paths
- optional labels or notes
- optional stop/continue policy hints

The format should remain simple and deterministic.

### 2) Queue model

Represent queue items with at least:

- task path
- ordinal position
- queue status (`queued`, `running`, `completed`, `blocked`, `failed`, `manual_patch`)
- short status note

### 3) Manifest validation

Validate that:

- task files exist
- duplicate task paths are either rejected or normalized by a clear rule
- queue items can be constructed deterministically from the manifest

### 4) No broad execution runner yet

This task is about representation and validation, not a full batch executor. It should provide the queue model that later tasks will consume.

## Tests

Add coverage that proves:

1. a valid task-list manifest becomes a deterministic queue
2. missing task files are surfaced clearly
3. duplicate task paths are handled by the chosen test-backed rule
4. queue status defaults are stable

## Documentation

Update the product spec and project state docs to describe the new task-list manifest and queue model as the first step toward autonomous backlog execution.

## Guardrails

- Do not add a broad scheduler yet
- Do not invent a highly dynamic task language
- Prefer a narrow manifest that later tasks can extend safely

## Acceptance

This task is complete when:

- a task-list manifest can be parsed into a deterministic queue
- validation errors are clear
- queue item state is well-defined
- tests remain green
