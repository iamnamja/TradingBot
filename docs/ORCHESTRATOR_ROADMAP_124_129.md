# Orchestrator Roadmap 124–129

This tranche follows the manual recovery of Task 123.

The goal is not to widen autonomy claims immediately. The goal is to make future orchestrator-run tasks actually complete by hardening compatibility-preserving self-heal and claim discipline.

## Why this tranche exists

Task 123 showed that the orchestrator can often identify the right failure area, but it still drifts on public/tested compatibility seams:

- alias fields on stable helpers
- project-contract convenience keys
- manifest schema aliases
- canonical stop-status vocabulary
- docs/spec claims getting ahead of green validation

This tranche turns those recurring failure modes into explicit contracts.

## Tasks

### 124 — Public compatibility contract freeze
Freeze the supported public/tested compatibility surfaces for the orchestrator-facing helpers and state/result payloads.

### 125 — Schema alias normalization layer
Create one canonical alias-normalization layer for task manifests, project contracts, and failure/remediation payloads.

### 126 — Canonical stop-status and decision vocabulary
Unify batch status, post-task decision, acceptance decision, and merge-posture vocabulary so the orchestrator cannot drift between near-synonyms.

### 127 — Assertion-driven self-heal targeting
Teach the repair planner to classify failing assertions into narrow seam categories and patch the smallest compatible surface first.

### 128 — Green-gated claim discipline
Prevent README / product-spec / project-state / roadmap claim drift unless focused and full validation are green.

### 129 — Supervised portfolio re-proof retry
After 124–128 are merged, rerun the bounded supervised portfolio proof as the capstone re-proof.

## Intended execution posture

- 124–128: manual-first
- 129: orchestrator-supervised, local-first, bounded
