# Task 190 — orchestrator contract and model transport checkpoint and next-slice gate

## Why

After Tasks 186–189, the repo needs another honest checkpoint: have docs consistency and model/output-contract hardening improved enough to plan a cautious bounded next slice, or should the project continue contract hardening first?

## Scope

Record a durable contract-and-model-transport checkpoint and next-slice gate.

## Runtime seams to reuse

- Reuse docs-status consistency truth from Task 186.
- Reuse model profiles and transport declarations from Task 187.
- Reuse dual transport support from Task 188.
- Reuse provider/model capability negotiation diagnostics from Task 189.
- Reuse the existing conservative checkpoint style already present in the repo.

## Requirements

- Produce a durable checkpoint that states whether the repo is:
  - not ready to plan the next slice,
  - conditionally ready under supervision,
  - or ready to plan a cautious bounded next capability slice
- Explicitly evaluate:
  - docs/status consistency enforcement,
  - model-profile explicitness,
  - Codex-compatible transport availability,
  - provider/model mismatch diagnostics and fallback discipline,
  - preservation of the proven GPT file-bundle path
- Keep the verdict conservative:
  - broad unattended multi-task autonomy remains blocked,
  - standalone productization remains blocked,
  - reopening the next slice only means cautious bounded planning may resume.

## Create or update these exact files

- `src/builder/orchestrator/model_transport_checkpoint.py`
- `tests/test_model_transport_checkpoint.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/190_orchestrator_contract_and_model_transport_checkpoint_and_next_slice_gate.md`

## Non-goals

- Do not claim broad multi-task autonomy.
- Do not unblock standalone orchestrator-app work.
- Do not skip directly to arbitrary scheduling or open-ended role routing.

## Acceptance criteria

- A durable contract/model-transport checkpoint artifact exists.
- Docs state clearly whether a cautious bounded next slice may be planned.
- Blocked areas remain explicit.
- Scope honesty is preserved.

## Implementation notes

- Keep the checkpoint additive and conservative, similar in tone to the bounded-corpus and reliability checkpoints.
- It is acceptable for the default verdict to remain conditionally ready under supervision if the evidence is incomplete.
