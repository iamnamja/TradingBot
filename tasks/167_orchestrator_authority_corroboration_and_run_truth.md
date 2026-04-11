# Task 167 — orchestrator authority corroboration and run truth

## Why

Even after the current reliability sprint, hosted-authority ambiguity still creates noise in the one-task lane. We need better corroboration so benchmark outcomes distinguish real authority blocks from timing artifacts without weakening conservative claim discipline.

## Scope

Improve authority corroboration and run-truth shaping while preserving the rule that unresolved authority ambiguity must not be silently treated as green.

## Requirements

- Reuse the existing hosted-authority and required-check truth surfaces where possible.
- Distinguish at least these cases inside benchmark/session artifacts:
  - likely CLI timing artifact,
  - unresolved authority ambiguity,
  - confirmed authority block.
- Persist the corroboration basis inside benchmark or re-proof artifacts.
- Keep the runtime conservative: unresolved ambiguity must not be treated as authority success.

## Create or update these exact files
- agents/run_task.py
- agents/lib/authority_gate.py
- tests/test_authority_gate.py
- tasks/167_orchestrator_authority_corroboration_and_run_truth.md
- docs/TRADINGBOT_PROJECT_STATE.md

## Acceptance criteria

- Tests prove that benchmark artifacts record authority corroboration state.
- Tests prove that unresolved ambiguity still prevents false “ready to widen” claims.
- Docs explain the benchmark-time authority truth model.

## Implementation notes

- Extended agents.lib.authority_gate with a lightweight corroboration classifier:
  - determine_corroboration_state() returns one of:
    - likely_cli_timing_artifact
    - unresolved_authority_ambiguity
    - confirmed_authority_block
  - decide_authority_gate() now supports an enriched mode (optional message/ok/step/classification)
    that returns a mapping with a corroboration_state while preserving legacy dataclass behavior
    when called with evidence only.
  - In enriched mode the mapping includes:
    - decision (hard_block | bounded_retry),
    - category (existing AuthorityEvidenceCategory value),
    - corroboration_state,
    - ok (explicit boolean; ambiguity/timing-artifact => False),
    - note, retry_limit, suggest_retry, step, message, and raw evidence echo.
- The runner’s failure-artifact writer uses these helpers via the thin wrappers already in
  agents/run_task.py and persists:
  - authority_corroboration: {state, category, decision, note, evidence…}
  - batch_checkpoint.authority_corroboration_state (plus mirrored fields)
- Runtime remains conservative: all ambiguity and timing-artifact cases return ok=False and
  suggest bounded retry only.

## Developer checklist

- Do not weaken POLICY_BLOCK or explicit required-check failures.
- Ensure enriched helpers are opt-in; do not break existing callers/tests expecting dataclass results.
- Persist corroboration state deterministically in placeholders and failure artifacts.
- Keep the corroboration classifier purely mechanical and derived from the hosted-authority truth surfaces and message text (no probabilistic inference).
