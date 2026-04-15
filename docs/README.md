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
- Task 195: transport stability checkpoint and cautious autonomy-resume gate

## Current next-step note

The near-term focus stays conservative:

- make transport failures observable instead of opaque
- guarantee either non-empty raw output capture or an explicit explanation of why capture is empty
- distinguish bundle parsing, method insertion, capability mismatch, and persistence failures quickly
- keep all new instrumentation additive and low-risk
- only consider capability widening after the post-195 checkpoint says transport stability is materially improved
