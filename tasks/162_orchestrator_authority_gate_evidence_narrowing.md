# Task 162: Orchestrator authority-gate evidence narrowing

Goal

Reduce false or over-broad authority blocks in the one-task lane by requiring narrower, more explicit evidence classification before the runner stops a task for authority reasons.

Scope

- Introduce a narrow classifier for authority-gate evidence categories.
- Distinguish at least:
  - no_checks_reported
  - explicit_required_check_failure
  - policy_block
  - ambiguous_or_missing_evidence
- Ensure the runner only hard-blocks when the evidence is explicit enough.
- For ambiguous evidence, prefer a bounded retry or a clearer failure artifact rather than an over-broad authority stop.
- Preserve the conservative project posture. This task should reduce noisy blocking, not weaken true authority gating.

Implementation notes

- A dedicated helper is exposed at `agents/lib/authority_gate.py`.
- The helper provides:
  - `AuthorityEvidenceCategory` enum of narrow categories.
  - `classify_authority_evidence(evidence)` to normalize incoming signals.
  - `decide_authority_gate(evidence)` to return a structured decision with:
    - `hard_block` (bool),
    - `category` (enum),
    - `reason` (str),
    - `suggest_retry` (bool),
    - `retry_limit` (int).
- Only explicit required-check failures or explicit policy blocks result in a hard stop.
- Ambiguous or missing signals prefer a bounded, low-amplitude retry to corroborate authority evidence.

Why this matters

The first reliability sprint improved transport, artifact hygiene, benchmark scorecarding, and completion integrity. The next biggest drag on one-task autonomy is that authority-style blocks can still stop otherwise-fixable tasks too early or with reasoning that is too broad to be actionable. By narrowing evidence categories and requiring explicit signals for hard blocks, we reduce noisy stops while preserving true authority protections.

Acceptance

- Helper surface exists and is covered by tests for explicit block, ambiguous evidence, and no-checks-reported paths.
- Runner logic can consume this helper to stay conservative while being more precise.
