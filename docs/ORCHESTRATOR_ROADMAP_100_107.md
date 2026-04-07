# Orchestrator Roadmap — Resilience and Hosted-Authority Hardening (100–107)

## Where this continuation starts

Task 099 synchronized the bounded multi-agent portability proof.

That proof is useful, but the recent misses on 097 and 099 showed that the orchestrator still struggles more with **proof-sync/public-surface drift** than with ordinary implementation work.

The next tranche should therefore prioritize resilience against those drift failures before broadening scope.

## Main gaps this tranche addresses

- public-surface symbol drift at pytest collection time
- result-shape drift in proof-facing tests
- manifest-schema drift (`path` vs `task_path`)
- docs/proof claims drifting beyond what exported surfaces actually support
- hosted CI authority semantics existing in code but not yet proven strongly in real branch flows
- repair loops choosing broad rewrites instead of minimal targeted compatibility patches

## Planned order

### 100 — Public surface freeze and compatibility aliases
Stabilize exported helper names and add explicit compatibility aliases for proof-facing/public surfaces.

### 101 — Collection-error and import-repair lane
Treat collection-time import/symbol failures as their own first-class repair strategy instead of generic red-test handling.

### 102 — Proof-sync contract validator and claim guard
Validate exported symbols, result shapes, manifest schema, and allowed proof claims before full pytest.

### 103 — Real hosted CI authority integration
Make hosted branch/PR check reporting and required-check truth stronger in real integrated flows, not only in local semantics.

### 104 — Result-shape and manifest-schema normalization
Normalize result fields and manifest entry schema through canonical adapters and compatibility surfaces.

### 105 — Targeted repair planner and minimal-patch selection
Bias repair toward the smallest compatible patch surface instead of rewriting broad proof bundles.

### 106 — External workspace bootstrap recovery proof
Prove truthful bootstrap failure and recovery across a simple external Python workspace shape.

### 107 — Supervised mixed-manifest autonomy re-proof
Run a supervised local-first orchestrator proof over a short mixed manifest spanning proof/docs, bootstrap, and consumer-facing task shapes.

## Expected lane mix

- **Manual first:** 100, 101, 102, 103, 104, 105, 106
- **Best supervised orchestrator candidate after those land:** 107

## Success criteria for this roadmap

This roadmap is successful when:

- collection-time import/public-surface drift stops causing repeated blind retry loops
- proof-facing surfaces are stable enough that bounded proof tasks stop guessing at names/fields
- docs/README claim drift is caught before full pytest
- hosted CI authority is stronger in real branch flows
- schema/result normalization reduces avoidable compatibility failures
- repair behavior becomes more targeted and less noisy
- one supervised mixed-manifest re-proof succeeds after those hardenings land
