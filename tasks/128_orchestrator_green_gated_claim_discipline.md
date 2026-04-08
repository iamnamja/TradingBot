# Task 128 — Orchestrator green-gated claim discipline

## Goal
Prevent docs/spec/README/state claims from moving ahead of actual green validation.

## Scope
- README
- docs/TRADINGBOT_PROJECT_STATE.md
- docs/ORCHESTRATOR_PRODUCT_SPEC.md
- roadmap/status text written by the orchestrator

## Required changes
- add a proof-claim gate that requires focused + full validation green before proof-complete wording is allowed
- add focused tests for claim blocking when checks are red
- keep docs updates narrow and truthful when recovery is still in progress

## Acceptance
- docs overclaim is blocked when validation is red
- proof-complete wording is allowed only after green validation
- full `ruff check .` and `pytest -q` are green
