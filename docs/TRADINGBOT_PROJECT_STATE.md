TradingBot Project State: Authority Gate Evidence Narrowing

Summary
The project continues to prioritize conservative safety and compliance gates. With the latest authority-gate evidence narrowing:
- Policy-driven blocks and explicit required-check failures still result in a hard stop.
- Ambiguous or missing evidence no longer triggers an over-broad hard stop; instead it should result in a bounded retry or clearer failure artifacts.

What changed
- A new helper at agents/lib/authority_gate.py classifies authority evidence into:
  - no_checks_reported
  - explicit_required_check_failure
  - policy_block
  - ambiguous_or_missing_evidence
- Runner code can use this helper to only hard-block on explicit cases, reducing noisy false positives without weakening true authority gating.

Operational posture
- The system remains conservative: any explicit policy block or required-check failure will halt the task.
- Ambiguous signals will not mask real failures; they simply avoid premature stopping and allow controlled retries or clearer diagnostics.

Next steps
- Continue to integrate the narrowed authority-gate classification across runners and controllers to ensure consistent, explicit gating decisions.
- Monitor logs for reduced noisy authority blocks and improved task autonomy in the one-task lane.
