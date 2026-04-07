# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 090–115 are complete:** the repo now has a canonical three-role multi-agent contract surface, persisted role handoff truth, stable typed coder/tester/controller artifact envelopes, a sequential builder/verifier/controller loop with controller-owned final authority, explicit verification-authority truth, a reusable Python-first project/workspace adapter contract, dependency-aware manifest planning/routing, a second-project Python portability proof, extraction-prep consumer boundary posture, targeted resilience hardening, external bootstrap recovery proof, supervised mixed-manifest re-proof, autonomy operating-mode hardening, and a supervised ordinary-manifest re-proof.

The current deterministic proof slice now demonstrates:

1. short ordinary-manifest progression across more than one ordinary task
2. truthful combined use of coder/tester/controller surfaces together
3. tester critique and focused replay before broader validation where relevant
4. repair-memory suppression of repeated no-progress attempts
5. bounded cross-task carry-forward memory
6. conservative stop behavior when authority or admission gates are unsatisfied
7. no broader claim than the deterministic local supervised proof covers

## Scope honesty

Current proof scope remains explicitly limited to:

- ordinary/non-protected task families
- deterministic local tests and stubs
- conservative stop-on-risk posture
- simple external Python project/workspace shapes through the adapter contract
- supervised short ordinary manifests bounded by `max_tasks`
- extraction preparation posture rather than completed standalone extraction

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Next continuation target

The next tranche should focus on moving from a bounded supervised ordinary-manifest proof toward the first credible multi-project portfolio operating mode.

That means prioritizing:

1. canonical project registry and per-project contracts
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. explicit next-task selection policy driven by backlog readiness and dependency truth
4. stronger repair planning with rollback-to-last-green
5. project-aware validation and authority profiles
6. hosted merge-eligibility convergence grounded in real repo contracts
7. a bounded supervised multi-project portfolio re-proof
