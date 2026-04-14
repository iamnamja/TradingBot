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

## Immediate continuation target (Tasks 191–195)

Run a transport-stability and observability tranche before any broader autonomy claims resume:

- 191 — raw model output capture integrity and non-empty artifact guarantee
- 192 — transport failure artifact expansion and parser-path observability
- 193 — protected-method preflight, fallback tracing, and retry discipline
- 194 — transport health benchmark and recurring failure-family corpus
- 195 — transport stability checkpoint and cautious autonomy-resume gate

## Why this tranche exists

The project now has enough contract/model clarity to see the real runtime problem:

- automated runs on some protected-surface and transport-sensitive tasks still fail before lint/tests,
- `_last_model_capability.txt` can report the selected model/transport as compatible,
- while `_last_agent_model_output.txt` can still end up effectively empty,
- and the parsed bundle artifact may reduce to `BEGIN_FILE_BUNDLE / END_FILE_BUNDLE` with no file entries.

That means the next bottleneck is not “model selection” in the abstract. It is “capture, persistence, and observability of transport failures.”
