# Orchestrator GitHub Required-Check Setup

This repo treats hosted-authority truth and unattended-readiness claims conservatively.

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

Use `ci-required` as the required status-check context for the TradingBot monorepo. Treat ad hoc job names as implementation details unless the contract is intentionally updated.

## Operational interpretation

When GitHub initially reports weak or incomplete evidence, the orchestrator should distinguish between:

- `not yet reported`
- missing required checks
- failed required checks
- weak or misconfigured enforcement

Initial `no checks reported` signals should not automatically be treated as final truth if the branch is still inside the settle window. Hosted authority should remain blocked until the stable `ci-required` contract actually appears and reaches a satisfiable state.

## Manual verification checklist

Before claiming unattended readiness, confirm that:

1. the repo contract expects `ci-required`
2. the GitHub ruleset or branch protection for `main` requires `ci-required`
3. pull requests actually publish `ci-required` on the branch
4. the required status reaches a passed state before merge progression
5. the repo can distinguish transient reporting delay from genuinely missing required-check evidence
