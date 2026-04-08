# Orchestrator Roadmap — Contracted Recovery and Convergence Quality (130–136)

## Where this continuation starts

Task 129 completed a bounded supervised local-first portfolio re-proof.

That matters, but the recent 129 failure also showed why the orchestrator is not yet ready to act like a low-babysitting central command system:

- a proof task was still under-specified enough to allow an empty file bundle
- the retry lane treated that failure too generically
- the model could patch tests/docs without repairing every coupled compatibility seam
- the repo’s hosted-authority story is still modeled more strongly than it is operationally enforced

The next tranche should therefore focus on **contracted recovery and convergence quality** rather than broader claims.

## Main gaps this tranche addresses

- task admission still allows some proof/re-proof tasks to reach the model without an explicit deliverable contract
- empty bundles, underfilled bundles, and zero-delta responses are not classified distinctly enough
- retry prompts are still too generic when missing-deliverable evidence is available
- assertion-driven repair is present, but it still misses some coupled public-surface / compatibility seams
- localized repair needs stronger last-known-good preservation and smaller rollback boundaries
- hosted-authority truth should stay honest when GitHub checks are missing, misconfigured, or not actually required

## Planned order

### 130 — Proof-task admission and exact-deliverable gate
Reject proof/re-proof tasks unless they declare exact repo-relative deliverables and the shell can compile a concrete expected-output contract before model invocation.

### 131 — Empty/underfilled bundle failure classification
Split empty bundle, underfilled bundle, markerless transport, and generic malformed bundle into distinct failure classes with distinct evidence and retry posture.

### 132 — Missing-deliverable retry compiler
When bundle transport is structurally valid but incomplete, compile the retry around exactly which required files are missing or unchanged instead of using a generic transport reminder.

### 133 — Assertion-to-compatibility surface planner
Expand assertion-driven repair so failing exported-key, snapshot, enum, and public-surface tests infer the full minimal coupled repair set instead of patching just one visible symptom.

### 134 — Last-green subset preservation and rollback
Persist the last-known-good accepted subset for a task attempt and roll back only the failing subset before targeted repair, so good files stop getting re-broken.

### 135 — Hosted-authority operational convergence probe
Tighten the repo-check contract so “no checks reported,” absent required checks, or weak branch-protection posture remain explicit blocking evidence for unattended claims.

### 136 — Supervised resilience re-proof
Re-prove the orchestrator on a bounded historical-failure corpus including empty bundle, underfilled bundle, coupled compatibility drift, no-ready-task stop posture, and hosted-authority unsatisfied evidence.

## Expected lane mix

- **Manual first:** 130, 131, 132, 133, 134
- **Manual or hybrid:** 135
- **Best orchestrator-supervised candidate after those land:** 136

## Success criteria for this roadmap

This roadmap is successful when:

- proof/re-proof tasks cannot silently reach the model without a concrete deliverable contract
- empty or incomplete bundle failures are recognized and repaired through targeted evidence
- retries focus on the missing files or missing compatibility seams rather than broad restatements
- good files are preserved while only failing subsets are repaired
- hosted-authority truth remains aligned with the repo’s real operational state
- the orchestrator can re-run the known painful failure classes with noticeably less babysitting than today
