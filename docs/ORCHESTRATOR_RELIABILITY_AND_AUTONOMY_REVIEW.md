# Orchestrator Reliability / Recovery / Autonomy Review

## Why this review exists

The orchestrator has become strong enough to enforce guardrails, but not yet strong enough to behave like a reliable central command system across a long backlog.

The current question is whether the bounded one-task lane is operationally trustworthy on real GitHub branches and understandable to an operator.

## Current strengths

- shell-routed execution and worktree/branch guardrails are present
- protected-file policies exist
- validator and failure-journal seams exist
- bundle preflight and localized repair support exist
- the repo now has a bounded one-task autonomous lane with ledger, canary reporting, supervised handoff, bounded resume state, and a live operator proof bundle

## Current weaknesses

### 1. The lane is still intentionally narrow
The repo can do one allowlisted safe task at a time, not broad unattended backlog execution.

### 2. Live GitHub timing still needs conservative interpretation
Real PR timing behavior should still be handled conservatively even with the new settle-window and real-PR smoke layers.

### 3. Self-hosting control-plane work still belongs in the supervised lane
This remains the right policy posture until separate live proof exists.

## Honest conclusion

The orchestrator can now be described as supervised and bounded, one-task autonomous inside a narrow allowlisted lane, and explicitly conservative outside that lane.
