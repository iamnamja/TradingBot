# Task 188a — orchestrator captured alternate payload fixture normalizer and apply adapter

## Why

Repeated attempts to execute this task have failed before code validation because the model response drifted away from the runner’s required `FILE:` / `END_FILE` bundle contract.

The next safe step is to prove the parsing and normalization logic using captured alternate-payload fixtures while keeping the task itself firmly in the normal file-bundle lane.

## Scope

Add a fixture-driven parser/normalizer and apply adapter for captured non-bundle payloads, without changing runner transport selection yet.

## Runtime seams to reuse

- Reuse the current GPT file-bundle parser unchanged for bundle-mode tasks.
- Reuse current safety checks after files are materialized.
- Reuse model-profile and transport declaration from Task 187 as metadata only.

## Requirements

- Add helper/library support for parsing and normalizing captured alternate payloads represented as text fixtures.
- Keep GPT file-bundle mode intact and default for the proven path.
- Add tests that would have caught the previous non-bundle payload mismatch in helper/library surfaces.
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
- Do not broaden capability claims beyond additive helper compatibility.
- Do not implement provider/model fallback logic yet.

## Acceptance criteria

- Helper/library surfaces can parse at least two payload shapes when given an explicit transport hint in tests or callers outside `agents/run_task.py`.
- GPT bundle mode remains green and unchanged.
- Alternate-payload parsing/normalization is additive and validated by tests.

## Delivery contract hardening

This run must still be delivered using the existing standard `FILE:` / `END_FILE` bundle format.

- The very first line of the assistant response must be `BEGIN_FILE_BUNDLE`.
- Do not emit prose before `BEGIN_FILE_BUNDLE`.
- Do not answer this task using diff output, raw `apply_patch` blocks, or any non-bundle transport.
- The alternate payload style is the subject being implemented and tested, not the response transport for this task run.
- The current run remains in the normal file-bundle lane so the orchestrator can validate and apply produced files.

## Implementation notes

- Prefer fixture-driven tests that feed captured alternate payload text into helper/library surfaces and assert normalized parsed operations or materialized file results.
- Keep parser/apply logic additive to the existing bundle parser rather than weakening bundle parsing rules.
- If needed, introduce a small adapter entrypoint in `agents/lib/bundle_parser.py` that dispatches between bundle parsing and alternate-payload parsing based on an explicit transport hint supplied by tests or callers outside `agents/run_task.py`.
- Avoid repeated use of the literal strings `patch`, `apply_patch`, or `diff` in code comments unless required by tests.
