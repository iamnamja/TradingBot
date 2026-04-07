# Task 108 — Orchestrator role handoff artifact envelopes and persistence

## Why this task exists

The current controller/builder/verifier split is real, but the role handoff payloads are still too loosely shaped and too easy to regress when adjacent work lands.

## Outcome

Add stable artifact envelopes for coder/tester/controller outputs and persist those envelopes explicitly in state and failure-journal surfaces.

## Create or update these exact files

- `agents/lib/controller_contract.py`
- `agents/lib/multi_agent_contract.py`
- `agents/lib/batch_state.py`
- `agents/lib/failure_journal.py`
- `agents/run_task.py`
- `tests/test_controller_contract.py`
- `tests/test_failure_journal.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`

## Required behavior

The artifact envelopes should, at minimum:

1. distinguish coder output from tester output from controller decision output
2. carry stable typed fields rather than ad hoc dict keys
3. persist round-trippable handoff payloads in batch/checkpoint state
4. persist the same envelope summaries in failure-journal context where relevant
5. remain explicitly sequential and deterministic

## Acceptance

This task is complete when the repo has stable persisted coder/tester/controller artifact envelopes and focused tests proving those envelopes survive round-trip persistence without broadening the current autonomy claim.
