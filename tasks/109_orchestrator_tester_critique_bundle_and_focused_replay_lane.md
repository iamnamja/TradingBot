# Task 109 — Orchestrator tester critique bundle and focused replay lane

## Why this task exists

The verifier/tester lane still leans too heavily on raw pytest blobs. For stronger self-heal, the tester should emit a more bounded critique bundle and focused replay guidance.

## Outcome

Add a tester critique bundle and focused replay lane that summarizes failure clusters, likely touched files, and replay commands.

## Create or update these exact files

- `agents/lib/check_runner.py`
- `agents/lib/failure_journal.py`
- `agents/lib/multi_agent_loop.py`
- `agents/run_task.py`
- `tests/test_failure_journal.py`
- `tests/test_multi_project_adapters.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The tester critique bundle should, at minimum:

1. summarize failing tests/files instead of only raw output
2. preserve a bounded replay command set (focused first, broad later)
3. identify whether the failure is likely import/contract/result-shape/docs drift vs broader execution failure
4. remain deterministic and local-first
5. stay compatible with the targeted repair planner rather than replacing it

## Acceptance

This task is complete when the verifier/tester lane emits a bounded critique bundle and focused replay guidance that can be consumed by controller repair logic and proven through focused tests.
