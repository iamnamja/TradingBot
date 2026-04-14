# Task 188 — orchestrator Codex patch transport and dual-mode output parsing

## Why

A `gpt-5-codex` run reached model output but failed in bundle transport because the harness still assumes a strict `FILE:/END_FILE` contract.

The repo needs a second additive transport path that can accept Codex-style patch/apply output while preserving the proven GPT bundle path.

## Scope

Add a Codex-compatible patch/apply transport and dual-mode parsing/apply logic.

## Runtime seams to reuse

- Reuse the current GPT file-bundle parser unchanged for bundle-mode tasks.
- Reuse current protected-surface and validation gates after files are materialized.
- Reuse model-profile and transport declaration from Task 187.

## Requirements

- Add a second output transport path for Codex-style patch/apply output.
- Keep GPT file-bundle mode intact and default for the proven path.
- Make the runner select the parser/apply mode from the declared transport contract.
- Keep artifact hygiene and safety checks consistent across both modes.
- Add tests that would have caught the previous “No FILE: blocks could be parsed” mismatch when the model was using a non-bundle-style output.

## Create or update these exact files

- `agents/lib/bundle_parser.py`
- `agents/lib/patch_apply.py`
- `agents/run_task.py`
- `tests/test_run_task_dual_transport.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/188_orchestrator_codex_patch_transport_and_dual_mode_output_parsing.md`

## Non-goals

- Do not remove the strict GPT file-bundle path.
- Do not claim full Codex parity across all tasks yet.
- Do not broaden capability claims beyond transport compatibility.

## Acceptance criteria

- The harness can distinguish and parse at least two transport modes.
- GPT bundle mode remains green and unchanged.
- Codex patch/apply mode is additive and validated by tests.
- Docs explain that this is compatibility hardening, not autonomy widening.

## Implementation notes

- Favor a narrow additive patch/apply adapter over rewriting the whole run loop.
