# Task 188b — orchestrator run_task dual transport selection and protected-surface integration

## Why

Once the normal-lane parser/apply adapter exists, the protected runner surface can be integrated narrowly. This keeps protected method mode focused on a single seam instead of mixing parser creation and runner integration in one task.

## Scope

Wire `agents/run_task.py` to select the parser/apply mode from the declared transport contract.

## Runtime seams to reuse

- Reuse the transport/parser helpers completed in Task 188a.
- Reuse model-profile and transport declaration from Task 187.
- Reuse current protected-surface and validation gates.

## Requirements

- Make the runner select the parser/apply mode from the declared transport contract.
- Keep GPT file-bundle mode intact and default for the proven path.
- Keep artifact hygiene and safety checks consistent across both modes.
- Add or extend tests only as needed for runner selection behavior.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_run_task_dual_transport.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/188b_orchestrator_run_task_dual_transport_selection_and_protected_surface_integration.md`

## Non-goals

- Do not rewrite the whole run loop.
- Do not remove strict GPT file-bundle rules.
- Do not claim full Codex parity across all tasks yet.

## Acceptance criteria

- The runner can inspect the declared transport contract and choose the correct parser/apply path.
- GPT bundle mode remains green and unchanged.
- Codex patch/apply mode is additive and validated by tests.
