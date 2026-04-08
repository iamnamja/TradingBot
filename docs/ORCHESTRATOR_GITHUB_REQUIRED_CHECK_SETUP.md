# Orchestrator GitHub Required-Check Setup

This repo now treats hosted-authority truth and unattended-readiness claims conservatively.

That means the code should only be considered operationally converged for unattended merge progression when the GitHub side is also aligned.

## Recommended GitHub configuration for `main`

Use a branch protection rule or ruleset that:

- requires a pull request before merge
- requires status checks to pass before merge
- uses the stable required-check context `ci-required`
- does not rely only on an incidental workflow job name as the long-term contract surface
- prevents force-pushes and direct bypasses unless explicitly intended for operators

## Why the repo contract uses a stable required-check name

The orchestrator needs a check name that is stable enough to treat as a contract surface.

Use `ci-required` as the required status check context for the TradingBot monorepo. Treat ad hoc job names as implementation details unless the contract is intentionally updated.

## What the runtime now verifies

Task 137 adds two distinct GitHub-side checks:

1. **Reporting truth** — whether pull requests actually report hosted checks on the branch (`gh pr checks`)
2. **Enforcement truth** — whether active branch rules or branch protection on the repo base branch actually require the configured `ci-required` context (`gh api repos/{owner}/{repo}/rules/branches/main` with fallback to `gh api repos/{owner}/{repo}/branches/main/protection`)

The orchestrator now treats both as required for unattended-readiness claims on the TradingBot monorepo.

## Operational interpretation

When the runtime sees any of the following, unattended readiness remains **blocked**:

- `no checks reported on the branch`
- branch rules / protection do not require `ci-required`
- GitHub enforcement requires a different status-check context than the repo contract
- GitHub enforcement could not be probed reliably

Local green validation alone is not enough to claim operational unattended readiness.

## Manual verification checklist

Before claiming unattended readiness, confirm that:

1. the repo contract expects `ci-required`
2. the GitHub branch protection rule or ruleset for `main` requires `ci-required`
3. pull requests actually report the check on the branch
4. the required check reaches a passed state before merge progression

## Useful GitHub CLI spot checks

```bash
gh pr checks --watch
gh api repos/{owner}/{repo}/rules/branches/main
gh api repos/{owner}/{repo}/branches/main/protection
```

The rules endpoint is the preferred signal because it returns the active rules that apply to the branch. The protection endpoint remains a compatibility fallback for repositories still relying on classic branch protection rather than rulesets.
