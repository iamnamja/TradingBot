# Task 188a — orchestrator Codex patch transport parser and apply adapter

## Why

The repo needs a second additive transport path that can accept Codex-style patch/apply output while preserving the proven GPT bundle path. The parser/apply adapter should be built first in the normal file lane before any protected runner integration.

## Scope

Add a Codex-compatible patch/apply adapter and dual-mode parsing primitives without wiring protected runner selection yet.

## Runtime seams to reuse

- Reuse the current GPT file-bundle parser unchanged for bundle-mode tasks.
- Reuse current safety checks after files are materialized.
- Reuse model-profile and transport declaration from Task 187.

## Requirements

- Add a second output transport path for Codex-style patch/apply output.
- Keep GPT file-bundle mode intact and default for the proven path.
- Add tests that would have caught the previous “No FILE: blocks could be parsed” mismatch when the model was using a non-bundle-style output.
- Keep all work in the normal lane; do not touch `agents/run_task.py` yet.

## Create or update these exact files

- `agents/lib/bundle_parser.py`
- `agents/lib/patch_apply.py`
- `tests/test_run_task_dual_transport.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/188a_orchestrator_codex_patch_transport_parser_and_apply_adapter.md`

## Non-goals

- Do not modify `agents/run_task.py` in this task.
- Do not remove the strict GPT file-bundle path.
- Do not broaden capability claims beyond transport compatibility.

## Acceptance criteria

- The repo can parse at least two transport modes in helper/library surfaces.
- GPT bundle mode remains green and unchanged.
- Codex patch/apply parsing is additive and validated by tests.
