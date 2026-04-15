# TradingBot + Orchestrator Monorepo

This repository contains:

- `src/tradingbot`: the trading bot runtime, strategy, risk, execution, and cycle components
- `src/builder/orchestrator`: the autonomous task-orchestration engine and reliability harness
- `agents/`: task execution harness, validators, and policy-aware run-task tooling
- `tasks/`: numbered implementation task specs and continuation plan docs
- `docs/`: project state, roadmap slices, and contributor-facing navigation

## Current continuation status

The synchronized reliability-and-promotion checkpoint is now complete through Task 195.

The repo can now honestly claim a materially hardened one-task lane with:

- proof-task admission gating on exact deliverable contracts
- strict no-manual-intervention benchmark scoring
- deliverable-contract and completion-integrity enforcement
- authority corroboration and conservative run truth
- empty-bundle retry shaping and durable transport diagnostics
- runtime-artifact hygiene and subset-preservation normalization
- a threshold-based promotion artifact for the one-task lane
- a defined default-path posture for eligible one-task work and an explicit two-task pilot gate
- a bounded supervised two-task canary benchmark flow and re-proof checkpoint integrated alongside the one-task artifacts
- a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus with a durable corpus benchmark and promotion/checkpoint artifact
- reliability-first import/public compatibility guardrails across benchmark and bounded-corpus entrypoints
- docs-status headline consistency guarding
- explicit model-profile declaration, dual-transport support, provider/model capability negotiation, and a conservative contract/model transport checkpoint through Task 190

Use `tasks/README.md` as the canonical task-order index, `docs/TRADINGBOT_PROJECT_STATE.md` as the authoritative status narrative, and `docs/ORCHESTRATOR_TRANSPORT_STABILITY_AND_OBSERVABILITY_191_195.md` as the operator-facing guide for the next tranche.

## What the repo can honestly claim today

Today the repo can honestly claim:

- benchmark-eligible one-task work is conditionally ready under supervision
- the orchestrator can complete real one-task runs and self-heal some failures
- a bounded supervised two-task pilot lane is ready and explicitly measured by canary and corpus-backed artifacts
- docs status consistency is guarded
- model profiles and transport contracts are explicit
- protected-method and bundle transport failures are now diagnosable enough to justify a focused observability tranche
- widening beyond the current bounded scope still requires proof, not aspiration

It does not claim:

- broad unattended multi-task autonomy
- general multi-agent role orchestration across arbitrary tasks
- fully reliable protected-method transport under automation
- full self-hosting control-plane autonomy
- a finished standalone orchestrator product

## Contract/model transport checkpoint (Task 190)

- Checkpoint verdict: conditionally ready under supervision.
- Meaning: a cautious bounded next slice may be planned only if it is aimed at stabilizing transport behavior and observability rather than widening autonomy.
- Blocked areas remain explicit: broad unattended multi-task autonomy and standalone productization stay blocked.

## Active tranche

Current active tranche: 196-200.

## Transport capture-result artifact (Task 191 addendum)

Transport failures now persist an explicit raw-output capture-result artifact:

- Path: `_last_raw_output_capture_result.json`
- Always written when transport diagnostics are emitted
- Classification values:
  - `non_empty` — raw output captured and non-empty
  - `empty_zero_length` — raw output file exists but length is zero
  - `empty_whitespace_only` — raw output contains only whitespace
  - `failed_before_payload` — capture failed before any payload was available
  - `truncated_or_redacted` — raw output was truncated or redacted for safety
- Related observability artifacts:
  - `_last_provider_call_path.txt` — provider/model/phase call path
  - `_last_raw_output_meta.txt` — raw-output meta including length and non-empty flags
  - `_last_agent_file_bundle_error.txt` — bundle-parse failure summary

These artifacts are additive and do not change the existing `_last_agent_model_output.txt` behavior; they make the emptiness case explicit rather than implicit.

## Transport failure details (Task 192)

Transport-failure artifacts are expanded to immediately surface parser-path and transport-contract context:

- Path: `_last_transport_failure_details.json`
- Fields include:
  - provider and model
  - required and selected transport, plus transport contract
  - parser path attempted (bundle vs method-insertion)
  - retry index
  - raw output length and basic capture classification parity
  - parsed bundle length and file-count, or method-block count for protected-mode
  - protected-method mode selected flag
  - short failure family/category
  - pointers to sibling artifacts (`_last_provider_call_path.txt`, `_last_raw_output_meta.txt`, `_last_agent_file_bundle_error.txt`)
- This artifact is machine-readable and small, and is written additively alongside the existing capture-result and bundle-error files.

## Protected-method preflight and retry discipline (Task 193)

Protected-method transport preflight and retry discipline are now explicitly traced:

- Protected-method preflight trace
  - Path: `_last_protected_method_preflight.json`
  - Captures why protected-method mode was selected, which paths were partitioned to protected vs normal bundle, and the capability negotiation snapshot for method insertion transport (including whether fallback was attempted/applied).
  - Includes a compact retry policy description for protected-method parsing.

- Retry-discipline trace
  - Path: `_last_retry_discipline_trace.json`
  - Captures the most recent execution phase, which retry phases were attempted, and whether fallback was attempted/applied.
  - Written additively alongside transport-failure artifacts to make retries explainable rather than opaque.

These traces reuse Task 189 capability negotiation and build on Tasks 191/192 observability artifacts. They are additive and do not change prior artifact formats or the acceptance path. Operators can inspect these JSON files to understand protected-method selection, capability fallback, and the applied retry strategy.

## Transport health benchmark and failure-family corpus (Task 194)

A small additive transport-health benchmark summarizes transport observability across a synthetic or live corpus:

- Summary fields:
  - run count,
  - empty-capture count,
  - bundle-parse failure count,
  - method-insertion failure count,
  - fallback count,
  - recurring failure-family counts.
- Artifacts written:
  - `_transport_health_summary.json`
  - `_transport_failure_families.json`

This benchmark is separate from trading runtime metrics and reuses the Task 191–193 observability seams.
- Code-level entrypoints:
  - `aggregate_transport_health(corpus)`
  - `write_transport_health(base_dir, summary, families)`
  - `compute_and_write_transport_health(corpus, base_dir)`

## Transport stability checkpoint and cautious autonomy-resume gate (Task 195)

A conservative transport-stability checkpoint evaluates:
- capture integrity,
- parser-path observability,
- protected-method fallback tracing,
- recurring transport failure-family rates,
- preservation of the proven GPT file-bundle path.

Checkpoint verdict: conditionally ready under supervision.
- Meaning: with transport observability now durable, a cautious bounded next slice may be planned only if it continues stabilizing transport behavior. Broader autonomy and any widening remain blocked until measurable reductions in empty-capture and parser-path failure rates are demonstrated across a larger corpus.
- Artifact: `_transport_stability_checkpoint.json` (additive; lives alongside transport-health artifacts).

## Active tranche

Current active tranche: 196-200.

