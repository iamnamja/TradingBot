# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 090–099 are complete:** the repo now has a canonical three-role multi-agent contract surface, persisted role handoff truth, a sequential builder/verifier/controller loop with controller-owned final authority, explicit verification-authority truth, a reusable Python-first project/workspace adapter contract, dependency-aware manifest planning/routing, a second-project Python portability proof, and an extraction-prep consumer boundary posture.

The current deterministic proof slice now demonstrates:

1. controller/builder/verifier role separation
2. dependency-aware short-manifest planning and routing truth
3. explicit verification-authority posture
4. Python-only second-project portability
5. extraction-prep consumer boundary posture rather than completed standalone extraction

## What recent failures taught us

The 097 and 099 misses were not broad core-loop failures. They exposed narrower resilience gaps:

- collection-time import/public-surface drift
- result-shape drift between proof tests and actual exported surfaces
- manifest-schema drift (`path` vs `task_path`)
- docs/proof-sync drift that should have been caught before full pytest
- hosted required-check authority still not behaving as a fully enforced external signal in practice

## Next planned tranche (100–107)

The next tranche should harden the orchestrator against those exact failure families before making broader autonomy claims.

Planned focus areas are:

- public-surface freeze and compatibility aliases for proof-facing helpers
- first-class collection-error/import-error repair routing
- proof-sync contract validation and claim guards before full pytest
- real hosted CI authority integration instead of mostly local semantics
- explicit hosted-authority availability vs satisfaction truth in branch/PR semantics
- result-shape and manifest-schema normalization
- targeted minimal-patch repair planning
- external workspace bootstrap recovery proof
- supervised mixed-manifest autonomy re-proof

## Near-term posture

Execution should remain intentionally sequential and deterministic.

Recommended lane mix for the next tranche:

- **100–105:** manual first
- **106:** manual first
- **107:** orchestrator-supervised, local-first

## Scope honesty

Current proof scope remains explicitly limited to:

- ordinary/non-protected task families
- deterministic local tests and stubs
- conservative stop-on-risk posture
- simple external Python project/workspace shapes through the adapter contract
- extraction preparation posture rather than completed standalone extraction

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.


## Hosted CI authority posture after 103

Hosted CI authority is now treated as first-class evidence in the truth model. The orchestrator distinguishes between:

- hosted checks were reported
- hosted checks were not reported
- hosted authority is available
- hosted authority is satisfied

This keeps `no checks reported on the branch` as an explicit stop signal rather than silently collapsing it into generic missing-check noise.
