# Orchestrator Roadmap 049–061 (Current Hardening / Integration Continuation)

## Tranche objective

Consolidate and stabilize the orchestrator after the completed 042–048 hardening baseline and the completed 049–054 continuity hardening steps, preparing for eventual repository/package extraction without claiming extraction is already complete.

## Status

- **042–048** — complete baseline
- **049–054** — complete on `main`
- **055–061** — current active continuation sequence

## Ordered roadmap

### Completed on main

1. **049** — run-task shell convergence umbrella
2. **049a** — run-task export/wrapper dedupe
3. **049b** — final shell routing extraction
4. **050** — public interface freeze
5. **051** — docs/status normalization
6. **052** — second-project portability proof
7. **053** — stable seam registry
8. **054** — task / seam preflight linter umbrella
9. **054a** — meta harness lane gate
10. **054b** — bundle preflight / localized repair

### Current continuation

11. **055** — integrated capability E2E flow
    - validate one real integrated flow using current live seams
    - keep focused failure-journal seam hardening in Task 056
12. **056** — failure-journal live seam
    - stabilize and document the failure-journal seam family
13. **057** — safe-parallelism / review integration
    - align planner/review coverage with the current live contract
14. **058** — runtime artifact quarantine integration
    - align quarantine integration coverage with live helper behavior
15. **059** — package extraction prep
    - complete technical/documentation preconditions for later extraction
16. **060** — canonical docs path policy
    - codify root-vs-`docs/` placement rules
17. **061** — task scope / split heuristics
    - teach the orchestrator when a task should be split across seam families

## Exit criteria for continuation completion

- Stable seam registry available for orchestrator integration tests.
- Preflight can catch common seam/task-shape mistakes before full iterations.
- One integrated capability flow validated against current live seams.
- Failure-journal, review, and quarantine seam families stabilized independently.
- Packaging/extraction prerequisites documented and satisfied.
- Canonical docs placement and task-splitting policy are explicit.

## Repo strategy note

Separation into a standalone orchestrator repository/package remains recommended **after** this continuation completes, not during current hardening.
