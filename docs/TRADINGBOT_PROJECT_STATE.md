# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 090–124 are complete:** the repo now has a canonical three-role multi-agent contract surface, persisted role handoff truth, stable typed coder/tester/controller artifact envelopes, a sequential builder/verifier/controller loop with controller-owned final authority, explicit verification-authority truth, a reusable Python-first project/workspace adapter contract, dependency-aware manifest planning/routing, a second-project Python portability proof, extraction-prep consumer boundary posture, targeted resilience hardening, external bootstrap recovery proof, supervised mixed-manifest re-proof, autonomy operating-mode hardening, supervised ordinary-manifest re-proof, project registry and isolation namespaces, backlog policy + dependency truth, bounded repair planning + rollback posture, project-aware validation/authority, hosted-authority convergence, and a supervised multi-project portfolio slice re-proof.

The current deterministic proof slice now demonstrates:

1. project selection across more than one registered project
2. isolated per-project state, branch, workspace, and carry-forward memory namespaces
3. frozen public/tested compatibility aliases for failure helpers, project contract convenience keys, manifest entry spellings, and manual-patch stop posture
3. next-task choice driven by explicit backlog policy and dependency truth
4. stronger self-heal with bounded repair planning and rollback where relevant
5. project-aware validation and authority evaluation
6. conservative stop behavior when portfolio scheduling or merge authority is unsatisfied
7. no broader claim than the deterministic local supervised proof covers

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation (`supervised_local_first`)
- bounded multi-project portfolio slices (not open-ended unattended scheduling)
- conservative stop-on-risk posture
- simple external Python project/workspace shapes through the adapter contract
- extraction preparation posture rather than completed standalone extraction

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Latest continuation checkpoint

Task 123 adds the bounded supervised local-first multi-project portfolio re-proof and synchronizes docs/tests to the exact claim boundary above.
