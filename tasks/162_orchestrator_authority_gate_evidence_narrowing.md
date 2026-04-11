Task 162: Orchestrator authority-gate evidence narrowing

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
- A dedicated helper surface is added at agents/lib/authority_gate.py providing:
  - classify_authority_evidence(evidence) -> AuthorityGateDecision
  - should_hard_block(evidence) -> bool
  - AuthorityEvidenceCategory enum for the four categories above.
- The design keeps default posture conservative: policy blocks and explicit required-check failures still stop execution. Ambiguous or missing evidence does not hard-block.

Tests
- tests/test_authority_gate.py covers explicit block, ambiguous evidence, no-checks-reported, and policy block paths.

Runtime-facing discipline
- This task remains runtime-facing and does not widen to multi-task logic.
- Required-check enforcement remains intact; only ambiguous evidence is softened to reduce noisy blocking.
