# Task 187 — orchestrator model profile registry and output transport contract

## Why

The harness currently treats model selection as flexible, but the output contract is still implicitly GPT-style file bundle mode.

The repo needs explicit model profiles and transport declarations so a Codex-style model is not forced through the wrong output contract.

## Scope

Define model profiles and an explicit output transport contract layer.

## Runtime seams to reuse

- Reuse current provider/model selection logic in `agents/lib/provider_client.py`.
- Reuse the existing strict file-bundle transport that works for the current GPT path.
- Reuse current run-task prompt/build flow rather than redesigning the whole harness.

## Requirements

- Introduce a model-profile registry or equivalent explicit mapping for supported model families.
- At minimum, represent:
  - GPT-style file-bundle mode
  - Codex-style patch/apply mode
- Add a public transport-contract declaration layer that the runner can inspect.
- Make the contract explicit enough that later tasks can choose the right parser/apply path.
- Preserve the known-good GPT file-bundle behavior exactly.

## Create or update these exact files

- `agents/lib/model_profiles.py`
- `agents/lib/provider_client.py`
- `agents/run_task.py`
- `tests/test_model_profiles.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/187_orchestrator_model_profile_registry_and_output_transport_contract.md`

## Non-goals

- Do not fully enable Codex patch transport yet.
- Do not silently change the default proven GPT path.
- Do not weaken bundle parsing rules for GPT-style tasks.

## Acceptance criteria

- A model-profile registry or equivalent exists.
- The runner can determine the expected output transport from the selected model/profile.
- Tests cover at least one GPT-style and one Codex-style profile expectation.
- Docs describe this as explicit contract declaration, not broader autonomy.

## Implementation notes

- Favor explicit profile metadata over string-matching spread across the codebase.
