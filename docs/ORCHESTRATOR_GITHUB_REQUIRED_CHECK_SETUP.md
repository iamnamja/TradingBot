# Orchestrator GitHub Required-Check Setup

This repo now treats hosted-authority truth and unattended-readiness claims conservatively.

That means the code should only be considered operationally converged for unattended merge progression when the GitHub side is also aligned.

## Recommended GitHub configuration for `main`

Use a branch protection rule or ruleset that:

- requires a pull request before merge
- requires status checks to pass before merge
- uses the stable required-check context `ci-required`
- does not rely only on the raw workflow job name as the long-term contract surface
- prevents force-pushes and direct bypasses unless explicitly intended for operators

## Why the repo contract uses a stable required-check name

The orchestrator needs a check name that is stable enough to treat as a contract surface.

Use `ci-required` as the required status check context for the TradingBot monorepo. Treat ad hoc job names as implementation details unless the contract is intentionally updated.

## Operational interpretation

When `gh pr checks` reports:

- `no checks reported on the branch`
- missing required checks
- weak or misconfigured enforcement

the orchestrator should remain truthful that unattended readiness is **not** established, even if local validation passed.

## Manual verification checklist

Before claiming unattended readiness, confirm that:

1. the repo contract expects `ci-required`
2. the GitHub branch protection/ruleset for `main` requires `ci-required`
3. pull requests actually report the check on the branch
4. the required check reaches a passed state before merge progression
