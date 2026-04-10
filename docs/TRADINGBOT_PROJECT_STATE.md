# TradingBot Project State

## Repository shape

The current monorepo contains:

- Trading runtime (`src/tradingbot`)
- Orchestrator engine and control plane (`src/builder/orchestrator`)
- Agent execution harness (`agents`)
- Numbered implementation tasks (`tasks`)
- Documentation and project-state tracking (`docs`)

## Current state

- **Tasks 124–153 are complete in bounded supervised scope:** the repo now freezes public/tested compatibility surfaces, normalizes schema aliases and canonical stop vocabulary, targets assertion-shaped failures toward coupled compatibility surfaces, gates proof tasks on exact deliverable contracts, distinguishes empty/underfilled/markerless/malformed bundle failures, compiles targeted retry prompts around missing deliverables, preserves the last-known-good subset while rolling back only the failing subset during retries, keeps hosted-authority operational convergence truth explicit, verifies real GitHub required-check enforcement convergence around the stable `ci-required` context, establishes a safe task-family autonomy allowlist, adds a bounded autonomous single-task runner with ledger/reporting/handoff/resume semantics, routes the scheduler through that runner when exactly one safe task is ready, packages the lane into an operator-readable live canary proof bundle, defines the canonical external-safe evaluation manifest, and now records a deterministic one-task developer / verifier / repair / controller loop inside each admitted safe run.

The current bounded deterministic slice now demonstrates:

1. supervised local-first portfolio progression across more than one registered project
2. project-scoped isolation for state, branches, workspaces, and carry-forward memory
3. dependency-aware next-task selection with conservative stop posture
4. compatibility-preserving hosted-authority truth and merge-eligibility truth
5. green-gated proof-claim discipline
6. targeted retry planning around missing deliverables and coupled compatibility surfaces
7. bounded subset preservation so targeted retries do not unnecessarily widen the changed-file set
8. explicit hosted-authority operational-readiness truth around the stable `ci-required` contract
9. a bounded autonomous one-task lane with scheduler bridging, explicit stop/requeue policy, supervised handoff, resume-state artifacts, and an operator proof bundle
10. a fresh supervised operational re-proof over the bounded one-task lane
11. a deterministic role-separated one-task execution record covering developer generation, verifier evidence, repair selection, and controller decision
12. an external-safe failure taxonomy and bounded self-heal router that chooses narrower repair lanes for common ordinary one-task failures
13. a durable pass-rate scoreboard and failure digest so operators can measure one-task completion, self-heal contribution, authority blocks, and dominant non-completion reasons from artifacts instead of anecdote
14. a fresh external-safe corpus reliability re-proof showing the current one-task autonomous pass-rate band is about two-thirds under supervised measurement, with bounded self-heal contributing materially to completion while hosted-authority and unsafe-work limits still hold

## Scope honesty

Current proof scope remains explicitly limited to:

- deterministic local supervised operation
- bounded multi-project portfolio slices
- conservative stop-on-risk / stop-on-authority-unsatisfied posture
- compatibility-preserving self-heal and schema alias normalization contracts
- safe-lane autonomy only for one allowlisted safe task at a time under supervision
- operator-readable proof for the bounded one-task lane, not broad autonomy

It still does **not** claim autonomy for arbitrary protected/controller/meta task lists, broad unattended production scheduling, arbitrary multi-task autonomous execution, or broad self-hosting control-plane autonomy.

## Next continuation target

The next tranche should shift from “more safe-lane plumbing” to **execution quality**:

1. define an external-style safe one-task evaluation corpus
2. make the bounded one-task lane behave like a real dev / test / repair / controller loop
3. improve targeted self-heal quality on ordinary external-safe failures
4. measure pass rate and failure-class distribution with durable scoreboard artifacts
5. re-prove the bounded one-task lane on that external-safe corpus against the measured baseline
6. only then decide whether bounded two-task trials are justified

## Task 149–153 checkpoint

Task 149 establishes the canonical external-safe evaluation manifest that later execution-quality tasks will use as the proving ground for one-task autonomous performance. The manifest carries:

- explicit archetype labels for ordinary external-style work
- allowed execution-lane truth per corpus item
- expected validation-profile truth per corpus item
- exact deliverable markdown text that later one-task runs can execute consistently

Task 150 converts each admitted one-task autonomous run from a simple shell around patch generation into a deterministic bounded multi-agent record. Each run now records:

- developer generation evidence and observed retry count
- verifier-focused and broad validation evidence
- tester-style critique and ordinary-task execution plan
- bounded repair-attempt selection derived from verifier evidence
- final controller action explaining whether the run was accepted, stopped, or escalated

Task 151 then adds an explicit external-safe failure taxonomy and self-heal router on top of that bounded loop. Ordinary one-task failures are now classified into narrower families such as:

- incomplete deliverable coverage
- missing required file updates
- import or collection errors
- focused test regressions
- lint-only failures

Those families now route into a smallest-credible repair plan instead of defaulting to a generic replay-only posture.

Task 152 converts that execution story into durable measurement. The bounded lane now emits a pass-rate scoreboard plus a failure digest so operators can see completed-without-manual-help runs, completed-after-self-heal runs, escalations, hosted-authority blocks, and the dominant reasons ordinary external-safe work still fails to complete.

Task 153 uses those artifacts for a fresh supervised re-proof over the canonical external-safe corpus. The current measured band is now truthfully stated as roughly **two-thirds pass rate (4 of 6)** on the bounded corpus, with **2 of the 4 completions** coming after bounded self-heal instead of manual intervention. The remaining non-completions stay bounded and informative rather than hidden: one lint-only failure and one hosted-authority/no-checks block. Unsafe or self-hosting work is still outside this re-proof and still escalates back to supervision rather than widening the claim.
