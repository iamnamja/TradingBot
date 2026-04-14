# Orchestrator Contract and Model Compatibility Guide (186–190)

## Goal of this tranche

The goal is to make the orchestrator less fragile in two ways:

1. narrative/status consistency should stop drifting across docs
2. model/output-transport assumptions should stop being implicit and GPT-specific

This is still reliability work. It is not a broad capability-expansion tranche.

## Current known problems

### 1) Docs/status drift
Recent tasks required manual cleanup because `README.md` and `docs/TRADINGBOT_PROJECT_STATE.md` did not always advance their status headlines together.

### 2) Codex output-contract mismatch
A `gpt-5-codex` task run reached model output but failed in bundle transport because the harness expects a strict `BEGIN_FILE_BUNDLE / FILE: / END_FILE / END_FILE_BUNDLE` protocol. That is a model/output-contract problem, not yet a proven general provider failure.

## What this tranche should accomplish

### Docs consistency
- one small source of truth or one validation rule for the repo status headline
- tests or guards that fail when key status docs drift

### Model profiles
- a registry or explicit mapping for model families and expected transport modes
- examples:
  - GPT bundle mode
  - Codex patch/apply mode
  - responses-only or tool-required flags where relevant

### Dual transport support
- keep the existing GPT file-bundle path intact
- add a Codex-compatible patch/apply path additively
- keep artifact hygiene and protected-surface rules intact regardless of transport

### Capability negotiation and fallback
- if a task requires bundle mode and the chosen model/profile does not satisfy that contract, fail early or fall back safely
- diagnostics should be explicit enough that operators can see whether the failure was:
  - provider/API compatibility
  - model-profile mismatch
  - malformed output for the selected transport

## Operator guidance

- continue using `gpt-5` as the known-good baseline until the Codex path is proven
- use narrow fixes only
- do not silently broaden capability claims because a second transport exists
- keep all new compatibility work additive and testable

## Expected checkpoint outcome (Task 190)

At the end of this tranche, the repo should be able to say:

- docs status consistency is guarded,
- model profiles are explicit,
- Codex-compatible transport exists or fails early with clear diagnostics,
- and a cautious next slice may be planned only if those contracts are stable under supervision.
