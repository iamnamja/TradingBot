# Task 163 — orchestrator runtime artifact quarantine and subset preservation normalization

## Goal
Make runtime artifact retention predictable during proof-mode runs so known-safe artifacts remain available for debugging while noisy leftovers like subset-preservation files do not repeatedly block clean autonomous completion.

## Why
Recent live runs succeeded technically but still produced manual-review friction because runtime leftovers were not normalized consistently.

## Requirements
- Normalize `_last_subset_preservation.json` handling so it is either retained as known-safe or avoided when not needed.
- Preserve `--keep-runtime-artifacts` behavior for the core debugging artifacts.
- Keep runtime artifacts unstaged by default.
- Do not weaken safety around truly unknown artifacts.

## Acceptance
- Successful proof-mode runs no longer stop on the same predictable leftover artifacts.
- Known-safe runtime artifacts remain available and unstaged.
- Tests cover artifact quarantine behavior for success and failure runs.
