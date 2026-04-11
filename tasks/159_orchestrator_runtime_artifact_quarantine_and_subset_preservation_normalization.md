# Task 159 — orchestrator runtime artifact quarantine and subset preservation normalization

## Why

The first proof-mode runs also surfaced confusing leftover artifacts such as `_last_subset_preservation.json` and parse-failure sentinels showing up as unknown manual-review leftovers. That makes successful runs harder to interpret and can distort operator trust.

## Scope

Normalize the runtime-artifact policy for proof-mode runs.

## Requirements

- Identify which runtime artifacts are known-safe and may remain unstaged after successful runs.
- Identify which runtime artifacts should be quarantined, deleted, or clearly marked as manual-review only.
- Make subset-preservation leftovers and bundle-transport diagnostics fit a deliberate policy instead of appearing as unknown noise.
- Keep runtime artifacts out of commits by default.
- Update operator-facing messaging so retained vs blocked artifacts are clearly explained.

## Acceptance criteria

- Tests prove that known-safe runtime artifacts are retained unstaged when requested.
- Tests prove that subset-preservation leftovers are either normalized into the known policy or quarantined with explicit explanation.
- Successful runs no longer report ambiguous “unknown runtime artifact” noise for artifacts covered by policy, including `_last_subset_preservation.json`.
- Docs explain the runtime-artifact policy for proof-mode runs.
