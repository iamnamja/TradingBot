# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 090–107 are complete:** the repo now has a canonical three-role multi-agent contract surface, persisted role handoff truth, a sequential builder/verifier/controller loop with controller-owned final authority, explicit verification-authority truth, a reusable Python-first project/workspace adapter contract, dependency-aware manifest planning/routing, a second-project Python portability proof, extraction-prep consumer boundary posture, targeted resilience hardening, external bootstrap recovery proof, and a supervised mixed-manifest re-proof.

The current deterministic proof slice now demonstrates:

1. controller/builder/verifier role separation
2. dependency-aware short-manifest planning and routing truth
3. explicit verification-authority posture
4. Python-only second-project portability
5. truthful external bootstrap blocked-then-recovered recovery
6. supervised mixed-manifest progression across proof/docs, bootstrap, and consumer-facing task families
7. conservative stop on unsatisfied authority
8. extraction-prep consumer boundary posture rather than completed standalone extraction

## What recent failures taught us

The 097, 099, and 107 misses were not broad core-loop failures. They exposed narrower resilience gaps:

- proof tasks still drift too easily toward broader public APIs than the repo actually exports
- compatibility wrappers and proof-facing adapters can regress when adjacent controller work lands
- the orchestrator still benefits from stronger coder/tester/controller handoff artifacts instead of loosely shared role context
- self-heal remains too stateless across repeated attempts and is still vulnerable to no-progress retries
- task admission is still too permissive for larger or more ambiguous task shapes
- hosted required-check authority is modeled more strongly in code than it is enforced in the live GitHub environment
- cross-task context carry-forward is still weak for broader autonomous backlog progression

## Next planned tranche (108–115)

The next tranche should shift from proof-hardening toward **autonomy operating mode hardening**.

Planned focus areas are:

- stable coder/tester/controller artifact envelopes and persisted role handoff payloads
- tester/verifier critique bundles with focused replay instead of only raw pytest blobs
- non-repeating repair memory and no-progress suppression
- safe task admission, family classification, and decomposition gates
- repo-scoped hosted-check contract and truthful environment probe behavior
- explicit multi-role task execution loop over ordinary tasks rather than only proof-facing role surfaces
- cross-task context carry-forward and bounded repo memory
- a new supervised end-to-end ordinary-manifest autonomy re-proof

## Near-term posture

Execution should remain intentionally sequential and deterministic.

Recommended lane mix for the next tranche:

- **108–113:** manual first
- **114:** manual or hybrid depending on how 113 lands
- **115:** orchestrator-supervised, local-first, bounded

## Scope honesty

Current proof scope remains explicitly limited to:

- ordinary/non-protected task families
- deterministic local tests and stubs
- conservative stop-on-risk posture
- simple external Python project/workspace shapes through the adapter contract
- supervised mixed-manifest slices bounded by `max_tasks`
- extraction preparation posture rather than completed standalone extraction

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, or broad multi-language portability.

## Hosted CI authority posture after 103

Hosted CI authority is now treated as first-class evidence in the truth model. The orchestrator distinguishes between:

- hosted checks were reported
- hosted checks were not reported
- hosted authority is available
- hosted authority is satisfied

This keeps `no checks reported on the branch` as an explicit stop signal rather than silently collapsing it into generic missing-check noise.

## Next product target after 107

The next product step should evolve the orchestrator from a stronger proof-backed project runner into a more explicit **multi-role autonomous ordinary-task runner**.

The intended next architecture is still intentionally conservative:

- **controller/orchestrator** decides what should happen next
- **builder/coder** proposes the narrowest plausible repo patch
- **tester/verifier** runs focused and full validation and summarizes bounded evidence

This should remain sequential before any future concurrency or true parallel role scheduling is considered.
