# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 090–129 are complete in deterministic supervised scope:** the repo now has a canonical three-role multi-agent contract surface, persisted role handoff truth, stable typed coder/tester/controller artifact envelopes, a sequential builder/verifier/controller loop with controller-owned final authority, explicit verification-authority truth, a reusable Python-first project/workspace adapter contract, dependency-aware manifest planning/routing, a second-project Python portability proof, extraction-prep consumer boundary posture, targeted resilience hardening, external bootstrap recovery proof, supervised mixed-manifest re-proof, autonomy operating-mode hardening, supervised ordinary-manifest re-proof, project registry/isolation/selection/authority/merge-eligibility proof, and post-123 compatibility/self-heal/claim-discipline hardening with Task 129 supervised portfolio re-proof retry.

The current deterministic proof slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. preserved project-scoped state, branch, workspace, and carry-forward isolation
3. dependency-aware next-task selection and conservative stop behavior when no dependency-ready task is available
4. compatibility-preserving hosted-authority truth and merge-eligibility truth after Tasks 124–128
5. green-gated docs/spec/status claim discipline for proof-complete wording
6. no broader claim than deterministic local supervised proof coverage

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- extraction preparation posture rather than completed standalone extraction

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Next continuation target

The next tranche should focus on reducing manual recovery frequency without widening autonomy claims.

That means prioritizing:

1. task admission rules that reject under-specified proof/re-proof tasks before the model is invoked
2. explicit failure classification for empty and underfilled bundles rather than treating them as generic malformed transport
3. targeted retry compilation around missing deliverables and missing-file evidence
4. better inference from failing assertions into the exact compatibility/public-surface seams that must be repaired together
5. preservation of last-known-good files while repairing only the failing subset
6. tighter operational convergence between local truth, hosted checks, and real branch-protection expectations
7. a bounded supervised re-proof over the historical failure classes that still cause babysitting today
