# Task 160 — Orchestrator completion integrity gate

## Goal
Prevent helper-only or new-surface-only bundles from being accepted as complete when the task clearly requires wiring into an existing live integration surface.

## Scope
- add a completion-integrity gate in the `agents.run_task` validation path after import validation and before writing files
- add a small helper module for parsing completion-integrity directives and evaluating the gate
- support machine-readable directives for tasks that need strict integration requirements
- keep the gate conservative and narrowly targeted so ordinary helper-only tasks can still pass when appropriate

## Completion Integrity Gate
- `REQUIRE_EXISTING_TOUCH: <path>` — path to an existing live surface that must be touched
- `MIN_EXISTING_NONTEST_TOUCHES: <int>` — minimum number of existing non-test/doc surfaces that must be edited
- `ALLOW_HELPER_ONLY: true|false` — whether a helper-only/new-surface-only bundle is acceptable

## Acceptance
- helper-only integration bundles are rejected with a retryable `completion_integrity` failure
- tasks with explicit directives can force required existing surface touches
- the gate does not break ordinary non-integration tasks
- focused tests cover directive parsing and helper-only rejection/acceptance
