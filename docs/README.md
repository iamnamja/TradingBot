# Docs Index Addendum

## Active tranche

Current active tranche: 191-195.

## Current roadmap slice

- `ORCHESTRATOR_ROADMAP_191_195.md` — transport stability and observability hardening after the post-190 checkpoint
- `ORCHESTRATOR_PHASE_DIRECTION.md` — agreed phase order: one-task truth first, bounded two-task pilot second, reliability hardening next, contract/model compatibility next, transport stability and observability next, cautious capability widening later, standalone app last
- `ORCHESTRATOR_TRANSPORT_STABILITY_AND_OBSERVABILITY_191_195.md` — operator-facing rules, artifact expectations, and working cadence for the 191–195 tranche

## Transport observability (Task 191)

Transport failures now persist an explicit capture-result artifact to remove ambiguity around empty outputs:

- Artifact: `_last_raw_output_capture_result.json`
- Status values:
  - `non_empty`
  - `empty_zero_length`
  - `empty_whitespace_only`
  - `failed_before_payload`
  - `truncated_or_redacted`
- Complementary artifacts: `_last_provider_call_path.txt`, `_last_raw_output_meta.txt`, `_last_agent_file_bundle_error.txt`

These are additive, hygiene-compatible, and preserve subset behavior. The legacy `_last_agent_model_output.txt` is still written; emptiness is now explicitly classified.

## Transport failure details (Task 192)

To make parser-path and contract choices immediately visible during failures, a compact machine-readable artifact is now persisted:

- Artifact: `_last_transport_failure_details.json`
- Captures provider/model, required/selected transport and contract, parser-path attempted (bundle vs method-insertion), retry index, raw-output length, parsed bundle file-count or method block count, protected-mode flag, and a short failure category.
- References sibling observability files so operators can pivot quickly to underlying payloads.

## Protected-method preflight and retry discipline (Task 193)

Protected-method selection and retry behavior are now explicitly traced:

- Preflight trace: `_last_protected_method_preflight.json`
  - why protected-method mode was selected (meta harness path, explicit target, or inference),
  - protected vs normal partition results,
  - capability negotiation snapshot for method-insertion transport, including fallback attempted/applied,
  - and the retry discipline policy for protected-mode parsing.

- Retry-discipline trace: `_last_retry_discipline_trace.json`
  - last phase and retry index,
  - attempted phases,
  - transport support compatibility snapshot,
  - fallback attempted/applied flags,
  - and pointers to sibling artifacts.

These artifacts reuse Task 189 capability negotiation and Tasks 191/192 transport observability. They are additive and keep default behavior unchanged.

## Transport health benchmark and failure-family corpus (Task 194)

A small transport-health benchmark aggregates results from transport observability artifacts and records:

- Fields summarized:
  - run count,
  - empty-capture count,
  - bundle-parse failure count,
  - method-insertion failure count,
  - fallback count,
  - recurring failure-family counts.
- Artifacts persisted:
  - `_transport_health_summary.json` — compact machine-readable summary
  - `_transport_failure_families.json` — recurring failure-family histogram

These remain separate from trading/runtime metrics and reuse the Task 191–193 artifacts.
- Code-level entrypoints:
  - `aggregate_transport_health(corpus)`
  - `write_transport_health(base_dir, summary, families)`
  - `compute_and_write_transport_health(corpus, base_dir)`

## Transport stability checkpoint and cautious autonomy-resume gate (Task 195)

A conservative transport-stability checkpoint evaluates capture integrity, parser-path observability, protected-method fallback tracing, recurring failure-family rates, and preservation of the proven GPT file-bundle path.

- Verdict: conditionally ready under supervision.
- Artifact: `_transport_stability_checkpoint.json` (additive to prior health artifacts).
- Gate: only a cautious bounded next slice focused on transport stability is in-bounds; broader autonomy remains blocked pending improved corpus evidence.

## Current continuation note

Tasks 186–190 completed the contract/model compatibility tranche:
- Task 186: docs status headline consistency guard
- Task 187: model profile registry and output transport contract declaration
- Task 188a: normal-lane alternate payload parser and apply adapter
- Task 188b: runner transport selection from declared contract
- Task 189: provider/model capability negotiation and safe fallback diagnostics
- Task 190: contract and model transport checkpoint plus conservative next-slice gate

Tasks 191–195 now target the next operational bottleneck:
- Task 191: raw model-output capture integrity and non-empty artifact guarantee
- Task 192: transport failure artifact expansion and parser-path observability
- Task 193: protected-method preflight, fallback tracing, and retry discipline
- Task 194: transport health benchmark and recurring failure-family corpus
- Task 195: transport stability checkpoint and cautious autonomy resume gate

## Current next-step note

The near-term focus stays conservative:

- make transport failures observable instead of opaque
- guarantee either non-empty raw output capture or an explicit explanation of why capture is empty
- distinguish bundle parsing, method insertion, capability mismatch, and persistence failures quickly
- keep all new instrumentation additive and low-risk
- only consider capability widening after the post-195 checkpoint says transport stability is materially improved
