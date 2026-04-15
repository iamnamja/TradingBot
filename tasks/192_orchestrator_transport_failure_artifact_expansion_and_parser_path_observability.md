# Task 192 — orchestrator transport failure artifact expansion and parser-path observability

## Why

Current failure artifacts do not make it easy to tell which parser path was attempted and why a particular transport failed.

## Scope

Expand transport-failure artifacts so parser path, contract, and artifact lengths are visible immediately.

## Runtime seams to reuse

- Reuse Task 191 capture-result truth.
- Reuse declared transport contract and capability negotiation outputs.
- Reuse existing transport-failure artifact files.

## Requirements

- Persist a richer transport-failure artifact that records:
  - provider and model,
  - required transport,
  - selected transport,
  - parser path attempted,
  - retry count,
  - raw output length,
  - parsed bundle length or method block count,
  - protected-method mode selection,
  - short failure family/category.
- Keep the artifact machine-readable and small.
- Add tests for bundle and method-insertion failure paths.

## Create or update these exact files

- `agents/run_task.py`
- `tests/test_bundle_transport_error_artifacts.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/192_orchestrator_transport_failure_artifact_expansion_and_parser_path_observability.md`

## Non-goals

- Do not broaden runtime behavior.
- Do not replace existing artifacts; extend them additively.

## Implementation notes

- The runner persists `_last_transport_failure_details.json` alongside existing artifacts, capturing parser-path, contract, and compact length/count fields.
- The artifact references `_last_provider_call_path.txt`, `_last_raw_output_meta.txt`, `_last_agent_file_bundle_error.txt`, and the last model/bundle payloads for quick pivoting.
- All new artifacts are additive and small; legacy file shapes remain unchanged.

## Tests added

- Bundle-path failure test verifies that an empty-bundle response writes a details artifact with:
  - provider/model, required/selected transport, parser path, retry index, and raw output length;
  - parsed-bundle file count equal to zero;
  - protected-method mode flag false.
- Method-insertion-path failure test verifies that protected-method mode selection and parser-path detection are recorded, with a stable method-block count field present.
