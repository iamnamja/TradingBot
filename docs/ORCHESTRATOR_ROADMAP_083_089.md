# Orchestrator Roadmap — Controller Contract Hardening (083–089)

## Where this continuation starts

Task 082 established the first narrow autonomous backlog-runner proof for a short ordinary manifest.

That was a real milestone, but it also showed where the next failure modes still live:

- controller contract drift between modules
- retry/self-heal semantics that can still be interpreted inconsistently
- merge/reset posture truth not fully canonicalized
- controller-task failures lacking strong semantic repair context
- controller patches that should be rejected earlier for low-discipline formatting/style drift

## Continuation goals

This tranche has six linked goals:

1. define one canonical controller contract module
2. make retry/self-heal explicitly non-reexecuting with separate execution vs repair truth
3. make merge/reset posture first-class persisted truth
4. improve controller-task repair guidance with semantic failure digests
5. add controller strict mode and pre-apply patch-quality gates
6. keep shrinking `agents/run_task.py` while preserving compatibility

## Planned order

### 083 — Controller contract canonicalization
Create one canonical controller contract module and make controller-facing helpers import it instead of restating literal sets independently.

### 084 — Non-reexecuting retryable self-heal channel
Make retry/self-heal semantics explicit so repaired results are re-validated without re-running raw execution attempts, and persist separate execution-vs-repair truth.

### 085 — Merge-posture truth persistence and resume contract
Treat `failed_merge`, `failed_checks`, and `failed_reset` as first-class terminal truth and make resume-after-merge depend on persisted evidence.

### 086 — Semantic failure digest and controller repair context
Generate a structured controller-failure digest in a helper module so repair prompts are driven by semantic drift, not only raw test logs.

### 087 — Controller-task strict mode and patch-quality gate
Apply stronger validation and pre-apply patch-quality rejection for controller-core tasks, and defer docs/proof claims until controller proof tests are actually green.

### 088 — Controller decomposition fourth extraction
Move more strict-mode and repair-context controller glue out of `agents/run_task.py`.

### 089 — Hardened autonomous short-manifest proof
Re-run the short ordinary-manifest autonomy proof after the above hardening and document the narrower-but-stronger claim honestly.

## Expected lane mix

- **Likely manual-patch / controller-core tasks**
  - 083
  - 084
  - 085
  - 086
  - 087
  - 088
- **Best autonomous candidate after those controller contracts land**
  - 089

## Success criteria for this roadmap

This roadmap is successful when:

- controller modules no longer drift on decision vocabulary or truth fields
- retryable self-heal no longer implies raw re-execution
- merge/reset posture is reflected truthfully in checkpoints/state
- controller-task repair gets a semantic failure digest
- obviously low-discipline controller bundles are rejected earlier
- `agents/run_task.py` is thinner again
- the hardened short ordinary-manifest proof is green and honestly documented

## “Can I feed it a list yet?” posture after this tranche

After 082: yes for a **short ordinary manifest proof slice**, but not as a broad claim.

After 083–089, the goal is to be able to say:

- short ordinary manifests can be run more reliably and with better self-heal/merge/reset truth
- controller-core and protected/meta tasks still remain a stricter/manual posture unless explicitly proven otherwise
