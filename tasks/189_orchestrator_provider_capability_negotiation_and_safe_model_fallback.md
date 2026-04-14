# Task 189 — orchestrator provider capability negotiation and safe model fallback

## Why

Even with explicit model profiles and dual transport, the runner still needs a clear answer to: “Can this provider/model satisfy this task’s required transport contract right now?”

The repo needs early capability negotiation and safe fallback or explicit diagnostics.

## Scope

Add provider/model capability negotiation and safe fallback diagnostics.

## Runtime seams to reuse

- Reuse model profiles and transport contracts from Task 187.
- Reuse dual transport parsing/apply logic from Task 188.
- Reuse current provider-client normalization and runtime artifact retention behavior.

## Requirements

- Before full model execution, determine whether the selected provider/model/profile can satisfy the task’s required output transport.
- On mismatch, do one of the following conservatively:
  - fail early with an explicit diagnostic, or
  - fall back to a configured safe model/profile
- Fallback must be explicit and inspectable, not silent.
- Persist enough diagnostic truth that operators can see whether a failure was:
  - provider/API capability mismatch,
  - model-profile mismatch,
  - or malformed output for the selected transport.

## Create or update these exact files

- `agents/lib/provider_client.py`
- `agents/lib/model_profiles.py`
- `agents/run_task.py`
- `tests/test_provider_model_capability_fallback.py`
- `README.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/README.md`
- `tasks/189_orchestrator_provider_capability_negotiation_and_safe_model_fallback.md`

## Non-goals

- Do not silently switch providers or models.
- Do not broaden capability claims based on a fallback alone.
- Do not remove explicit diagnostics in favor of hidden retry behavior.

## Acceptance criteria

- The runner can detect a model/profile/transport mismatch before late bundle transport failure.
- Tests cover at least one explicit mismatch and one safe fallback or explicit-stop path.
- Diagnostics are durable enough to explain what went wrong.
- Docs describe this as contract hardening, not capability widening.

## Implementation notes

- Favor explicit “required transport vs provided transport” checks over implicit trial-and-error.
