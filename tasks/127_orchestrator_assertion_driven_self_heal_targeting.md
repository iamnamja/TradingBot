# Task 127 — Orchestrator assertion-driven self-heal targeting

## Goal
Make the repair planner classify assertion failures into narrow seam categories and patch the smallest compatible surface first.

## Scope
- missing alias
- missing exported key
- wrong canonical enum/value
- missing project contract field
- docs overclaim while tests are red

## Required changes
- add assertion-shape classification helpers
- rank narrow compatibility fixes above broad freeform rewrites
- surface the chosen repair target explicitly in failure artifacts

## Acceptance
- focused tests prove narrow seam selection on representative failures
- repair planning remains bounded and deterministic
- full `ruff check .` and `pytest -q` are green
