# TradingBot Project State

Overview

This repository contains a self-contained trading bot with an orchestrator and a comprehensive test harness. Recent reliability sprints focused on:
- transport stability and artifact hygiene,
- benchmark scorecarding,
- completion integrity and contract discipline.

Authority gating posture

- The orchestrator integrates external and project policy authority (e.g., required CI checks, repository policies).
- Authority gating remains conservative: explicit required-check failures or explicit policy blocks will stop progression.
- The signal handling has been narrowed to reduce false or over-broad stops:
  - no_checks_reported → prefer a bounded retry to corroborate, not a hard stop.
  - ambiguous_or_missing_evidence → prefer a bounded retry and clearer failure artifact.
  - explicit_required_check_failure → hard stop with explicit reason.
  - policy_block → hard stop with explicit reason.
- This makes authority decisions more actionable while maintaining strict enforcement where the evidence is explicit.

Notes

- No production integrations are widened by default. Any external execution remains opt‑in and deterministic.
- The runner continues to honor required checks and policy profiles without weakening enforcement.
