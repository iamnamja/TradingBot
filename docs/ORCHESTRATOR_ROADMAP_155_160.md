# Orchestrator Roadmap 155–160

This roadmap starts after Task 154 established the explicit go / no-go gate for bounded two-task trials.

The truthful outcome after that gate is **no-go for widening**. The next tranche therefore should not widen the lane yet. It should remove the most ordinary preventable blockers inside the one-task lane until the gate inputs improve honestly.

## Why this tranche exists

The current measured one-task band is promising but not yet good enough to justify bounded two-task trials. Two blockers stand out:

- a preventable lint-only non-completion on external-safe work
- hosted-authority / no-checks noise that still forces conservative blocking

This tranche should improve the current lane instead of widening it prematurely.

## Intended direction

### 155 — Safe lint preflight normalization
Convert isolated lint-only failures on required Python paths into a bounded normalization pass before the run is recorded as failed.

### 156 — Hosted-authority corroboration for admitted safe tasks
Separate transient GitHub CLI no-checks noise from stronger hosted-authority evidence while keeping claim discipline conservative.

### 157 — Direct-completion bias for ordinary one-task work
Reduce repair dependence by preferring first-pass hygiene and smaller replay scopes when the builder already landed near-green work.

### 158 — Gate-blocker trend reporting
Extend reporting so operators can see which readiness-gate inputs are improving and which ones still keep the lane in no-go posture.

### 159 — Corpus refresh after blocker reduction
Re-measure the external-safe corpus after blocker-reduction changes instead of relying on stale scoreboards.

### 160 — Two-task readiness re-proof
Re-evaluate the Task 154 gate only after the blocker-reduction tranche produces new measured evidence.

## Desired outcome

By the end of this tranche, the repo should be able to say:

- the one-task lane removes preventable lint-only drift automatically where safe
- hosted-authority blocking is corroborated more carefully without widening claims
- direct completions improve relative to repair-heavy completions
- the two-task gate is reconsidered only on fresh evidence
