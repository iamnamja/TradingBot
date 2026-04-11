# Task 162: orchestrator authority-gate evidence narrowing

Goal

Reduce false or over-broad authority blocks in the one-task lane by requiring narrower, more explicit evidence classification before the runner stops a task for authority reasons.

Why this matters

The first reliability sprint improved transport, artifact hygiene, benchmark scorecarding, and completion integrity. The next biggest drag on one-task autonomy is that authority-style blocks can still stop otherwise-fixable tasks too early or with reasoning that is too broad to be actionable.

Create or update these exact files
- agents/run_task.py
- agents/lib/authority_gate.py
- tests/test_authority_gate.py
- tasks/162_orchestrator_authority_gate_evidence_narrowing.md
- docs/TRADINGBOT_PROJECT_STATE.md

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

Acceptance criteria
- There is a dedicated authority-gate helper surface in `agents/lib/authority_gate.py`.
- `agents/run_task.py` uses the narrowed authority-gate classification instead of broad ad hoc checks.
- Tests cover explicit block, ambiguous evidence, and no-checks-reported paths.
- Project state docs explain that authority gating is still conservative but now more explicit and narrower.

Notes
- Keep this task narrowly runtime-facing.
- Do not widen to multi-task logic.
- Do not weaken required-check enforcement.
