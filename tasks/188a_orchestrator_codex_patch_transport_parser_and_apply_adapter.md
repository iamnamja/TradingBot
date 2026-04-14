# Task 188a — codex patch payload fixture parser and apply adapter (normal lane)

## Why

Repeated attempts to execute the original Task 188a failed before lint/tests because the model confused the *subject being implemented* with the *response transport it should use for the task run*.

We need a narrower normal-lane step that proves the parser/adapter logic on captured Codex-style patch payloads **without** touching protected runner surfaces and **without** changing the task-response format used by this orchestrator.

## Scope

Implement a fixture-driven Codex patch payload parser/apply adapter in the normal lane only.

This task is intentionally limited to:
- additive helper logic for parsing and normalizing Codex-style patch/apply payload text,
- fixture-driven tests,
- additive documentation of the narrowed intent.

This task does **not** integrate the new adapter into `agents/run_task.py` or change the active default transport.

## Delivery contract for this task run

Even though this task is about Codex-style patch/apply payloads, the assistant must still deliver **this task's changes** using the standard repository task response format:

- `BEGIN_FILE_BUNDLE`
- `FILE: <path>`
- file contents
- `END_FILE`
- `END_FILE_BUNDLE`

Do **not** respond in unified diff form, patch blocks, `apply_patch` blocks, or any non-`FILE:` transport for this task run.

The patch/apply payload is the implementation subject, not the response format.

## Runtime seams to reuse

- Reuse the explicit model-profile and transport-contract declaration added in Task 187.
- Reuse existing bundle and parsing vocabulary where possible, but keep this task in normal non-protected files.
- Reuse additive helper/test patterns already used in the reliability tranche.

## Requirements

- Add a narrow helper that can parse and normalize a Codex-style patch/apply payload captured as plain text fixture input.
- The helper must return a deterministic, machine-consumable structure that later tasks can feed into runner integration.
- Support at least:
  - extraction of one or more file targets,
  - extraction of replacement/apply operations or normalized patch sections,
  - explicit failure signaling when the payload is malformed or incomplete.
- Keep the work additive and normal-lane only.
- Add tests using static fixtures or inline text samples.
- Preserve the proven GPT file-bundle default path exactly.

## Create or update these exact files

- `agents/lib/codex_patch_adapter.py`
- `tests/test_codex_patch_adapter.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/188a_orchestrator_codex_patch_transport_parser_and_apply_adapter.md`

## Non-goals

- Do not modify `agents/run_task.py`.
- Do not modify protected method-mode parsing or insertion machinery.
- Do not enable Codex transport selection yet.
- Do not weaken strict GPT file-bundle parsing.
- Do not respond using diff/patch text instead of normal file bundles.

## Acceptance criteria

- A normal-lane helper exists for parsing and normalizing Codex-style patch/apply payload text.
- Tests cover at least one valid payload and one malformed payload.
- The default GPT file-bundle execution path remains unchanged.
- Docs describe this as a parser/adapter proof step, not a transport switch.

## Implementation notes

- Favor fixture-driven parser normalization over broad runtime integration.
- Return explicit structured data rather than side effects.
- Keep file targets and operation ordering deterministic.

## Implementation intent note

This task has been deliberately narrowed after repeated bundle-transport failures. The correct success condition is proving the parser/adapter logic in isolation, not changing the orchestrator’s own response transport or protected runner behavior.
