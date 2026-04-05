# Task 096 — Orchestrator task-family router and agent selection

## Why this task exists

Once the orchestrator has explicit multi-agent roles and a dependency-aware planner, it still needs a reliable way to choose which role should act next for a given task family.

The controller should be able to distinguish, for example:

- code-building tasks
- verification-only tasks
- proof/docs synchronization tasks
- bootstrap/setup tasks
- manual/protected/controller-core tasks that should remain constrained

## Outcome

Introduce a task-family router that chooses the next eligible role/lane for the current task and failure posture.

## Create or update these exact files

- `agents/lib/agent_router.py`
- `agents/lib/task_contracts.py`
- `agents/lib/multi_agent_loop.py`
- `agents/run_task.py`
- `tests/test_run_task_contract_directives.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_CONTROLS_AND_POLICIES.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

### 1) Canonical task-family routing

At minimum support routing decisions for:

- builder-first tasks
- verifier-first tasks
- proof/docs tasks
- bootstrap/setup tasks
- strict/manual controller-core tasks

### 2) Controller-owned selection

The router should recommend, but the controller remains the authority that selects the next role/lane.

### 3) Strict-mode compatibility

Controller-core or proof-shaping tasks should continue to respect strict-mode guardrails.

### 4) Resume-safe routing truth

Persist enough routing metadata that a resumed run can explain why a role/lane was chosen.

## Tests

Add or adjust deterministic tests that prove:

1. task-family routing chooses the expected candidate role/lane
2. controller can override or stop rather than follow a risky router suggestion
3. strict-mode tasks still route into constrained lanes
4. routing truth is persisted and visible to resume/debug surfaces

## Guardrails

- Do not allow the router to bypass controller authority
- Keep manual/protected/controller-core limits honest
- Prefer a small, inspectable set of task families over uncontrolled heuristics
- Preserve compatibility for existing task contract directives

## Acceptance

This task is complete when the orchestrator can choose between builder, verifier, and constrained/manual lanes based on canonical task-family routing rather than one generic path.
