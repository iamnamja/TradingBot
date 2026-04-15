# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state (post-Task 190)

- Tasks 157–190 are complete in bounded supervised scope.
- The repo now has:
  - a strict no-manual-intervention one-task scorecard,
  - deliverable-contract and completion-integrity enforcement,
  - authority corroboration and conservative run truth,
  - narrowed top one-task failure-family handling,
  - a durable one-task promotion verdict,
  - an explicit default one-task path,
  - a conservative two-task pilot admission gate,
  - a bounded adjacent-task A->B handoff contract,
  - a supervised builder/verifier role split scoped for the pilot,
  - a durable two-task canary scorecard and benchmark artifacts integrated into the existing benchmark session directory,
  - a real bounded two-task pilot runner exercised over a curated adjacent-pair corpus,
  - a bounded two-task pilot re-proof with explicit canary and corpus-backed promotion payloads,
  - reliability benchmark artifacts and a regression matrix,
  - docs-status guarding,
  - explicit model-profile and transport declaration,
  - additive dual-transport support,
  - provider/model capability negotiation and fallback diagnostics,
  - a durable contract/model transport checkpoint (Task 190).

## Honest current posture

- One-task lane: conditionally ready under supervision for benchmark-eligible work (default path).
- Two-task lane (bounded pilot): ready for a bounded supervised two-task pilot on the curated adjacent-pair corpus, governed by admission, handoff, and role-split truth and measured by conservative canary scorecards and corpus-backed `two_task/bounded_corpus` artifacts.
- Contract/model transport checkpoint (Task 190): conditionally ready under supervision to plan a stability-and-observability tranche. This does not unblock unattended multi-task autonomy or standalone productization.

This means:

- one-task work remains the default proving path under light supervision,
- the two-task pilot can proceed in a bounded, supervised manner on the curated corpus,
- the transport/model layer is more explicit than before but still not operationally robust,
- broad multi-task autonomy is still not justified,
- and the standalone orchestrator-app phase remains blocked behind stronger autonomy and runtime proof.

## What still blocks the next phase

Before broad multi-task autonomy or product extraction can be justified, the repo still needs:

- sustained two-task corpus evidence from real bounded pilot runs across curated adjacent-task pairs,
- lower supervised-intervention rates on the bounded pilot lane,
- durable pair-level ledgers that distinguish autonomous progress from operator help,
- additional authority-corroboration truth and failure-family elimination for multi-task sequences beyond the first adjacent pair,
- better resume-safe recovery so partially-successful runs re-enter from precise checkpoints instead of broad retries,
- transport-failure observability that preserves non-empty raw output or explains why it is empty,
- explicit protected-method preflight and fallback traces,
- faster diagnosis of bundle vs method-insertion vs capture failures,
- and a measurable reduction in transport-related empty-output failures.

## Active tranche

Current active tranche: 191-195.

## Immediate continuation target (Tasks 191–195)

Run a transport-stability and observability tranche before any broader autonomy claims resume:

- 191 — raw model output capture integrity and non-empty artifact guarantee
- 192 — transport failure artifact expansion and parser-path observability
- 193 — protected method preflight, fallback tracing, and retry discipline
- 194 — transport health benchmark and recurring failure-family corpus
- 195 — transport stability checkpoint and cautious autonomy resume gate

## Transport capture-result (Task 191)

To remove ambiguity when `_last_agent_model_output.txt` is empty or whitespace-only, every transport failure now persists:

- `_last_raw_output_capture_result.json` — explicit classification of capture outcome:
  - `non_empty`, `empty_zero_length`, `empty_whitespace_only`, `failed_before_payload`, `truncated_or_redacted`
- `_last_raw_output_meta.txt` — raw-output meta (length, non-empty flags, provider/model/phase)
- `_last_provider_call_path.txt` — provider/model transport call-path trace

These artifacts are additive and follow repository hygiene and subset-preservation rules.

## Transport failure details (Task 192)

To speed operator diagnosis and preserve small, machine-readable observability, transport failures also persist:

- `_last_transport_failure_details.json` — provider/model, required/selected transport, transport contract, parser path (bundle vs protected method), retry index, raw-output length, parsed bundle file-count or method-block count, a protected-mode flag, and a short failure category, with pointers to sibling artifacts.

## Protected-method preflight and retry discipline (Task 193)

- Preflight trace: `_last_protected_method_preflight.json`
  - Captures why protected-method mode was selected, the protected vs normal partition, and a capability-negotiation snapshot for method-insertion transport (including whether fallback was attempted/applied).
  - Includes a compact description of the retry discipline policy that will be applied under protected-mode parsing.

- Retry discipline: `_last_retry_discipline_trace.json`
  - Provides a terse, machine-readable log of which protected-method retry phases were attempted (initial vs retry), the latest retry index, and fallback attempted/applied flags, with pointers to the sibling capability and preflight artifacts.

These are additive artifacts that reuse Task 189 capability negotiation and the Task 191/192 observability foundation.

## Transport health benchmark and failure-family corpus (Task 194)

The orchestrator now includes a small additive transport-health benchmark that summarizes corpus-backed transport outcomes:

- Fields summarized:
  - run count,
  - empty-capture count,
  - bundle-parse failure count,
  - method-insertion failure count,
  - fallback count,
  - recurring failure-family counts.
- Artifacts:
  - `_transport_health_summary.json` — compact benchmark summary
  - `_transport_failure_families.json` — recurring failure-family histogram

These measurements remain separate from trading/runtime metrics and reuse the Task 191–193 observability seams to quantify whether transport health is improving.
- Code-level entrypoints:
  - `aggregate_transport_health(corpus)`
  - `write_transport_health(base_dir, summary, families)`
  - `compute_and_write_transport_health(corpus, base_dir)`
