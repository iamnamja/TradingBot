# Task 158 — orchestrator authority corroboration and run truth

## Why

Hosted-authority ambiguity still creates friction in the one-task lane. We intentionally kept the runtime conservative around required-check truth, but the system needs better corroboration so benchmark results are not overly noisy.

## Scope

Improve benchmark-time authority corroboration while preserving conservative claim discipline.

## Requirements

- Reuse the existing hosted-authority / required-check truth surfaces where possible.
- Add corroboration logic or artifact shaping that distinguishes:
  - likely CLI timing artifact,
  - unresolved authority ambiguity,
  - confirmed authority block.
- Persist the corroboration basis inside benchmark artifacts.
- Do not weaken the rule that unresolved authority ambiguity must not be silently treated as green authority.

## Acceptance criteria

- Tests prove that benchmark artifacts record authority corroboration state.
- Tests prove that unresolved ambiguity still prevents false “ready to widen” claims.
- Docs explain the benchmark-time authority truth model.
