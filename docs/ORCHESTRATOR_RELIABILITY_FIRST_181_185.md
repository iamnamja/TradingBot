# Orchestrator Reliability First 181–185

## Operator intent

This slice is not about adding broader capability first. It is about making the current one-task and bounded two-task lanes more dependable.

## What to optimize for

Optimize for:

- fewer recurring failure families,
- narrower repair targets,
- fewer compatibility regressions,
- clearer resume/re-entry behavior,
- lower supervision rate on bounded work,
- lower retry count to green.

Do not optimize for:

- broader task depth,
- arbitrary agent routing,
- new productization claims,
- standalone app work.

## Working rules

- Review merged-main snapshots first.
- Prefer narrow patches.
- Treat one-task truth surfaces as protected compatibility surfaces.
- Treat bounded two-task benchmark and corpus artifacts as additive surfaces.
- If the failure is task-admission or exact-deliverable-contract related, harden the task contract first instead of guessing at code.
- If the failure is compatibility/import related, patch the public contract narrowly instead of rewriting runtime modules broadly.
- If a run partially succeeds, prefer checkpointed resume or re-entry over a broad retry.

## Expected artifacts in this slice

Reliability-oriented work should produce or update artifacts such as:

- failure-family taxonomy / classification truth,
- repair-target selection truth,
- resume checkpoint / attempt-state truth,
- reliability benchmark or regression matrix artifacts,
- an explicit post-185 reliability checkpoint and capability-resume gate.

## Merge posture

Merge only when:

- diffs are narrow,
- compatibility surfaces remain intact,
- benchmark and task-admission surfaces stay additive and honest,
- and validation is green from a clean branch.

## What this slice should unlock later

If Tasks 181–185 succeed, the next slice may cautiously reopen:

- wider curated two-task corpora,
- limited role-routing decisions under policy,
- carefully-curated three-step sequences.

If they do not, the correct result is to stay reliability-first longer.
