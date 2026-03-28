# Orchestrator Roadmap 049–068 (Reliability / Recovery / Autonomy Reset)

## Tranche objective

Complete the already-landed 049–054 shell/harness hardening work, then pause the original continuation and insert a Reliability / Recovery / Autonomy tranche before resuming the deferred continuation items.

## Status

- **049–054b** — complete on `main`
- **055–061** — active next tranche (Reliability / Recovery / Autonomy)
- **062–068** — deferred continuation after reliability tranche

## Ordered roadmap

### Completed on main

1. **049** — run-task shell convergence umbrella
2. **049a** — run-task export/wrapper dedupe
3. **049b** — final shell routing extraction
4. **050** — public interface freeze
5. **051** — docs/status normalization
6. **052** — second-project portability proof
7. **053** — stable seam registry
8. **054** — task/seam preflight linter umbrella
9. **054a** — meta harness lane gate
10. **054b** — bundle preflight / localized repair

### Active next tranche — Reliability / Recovery / Autonomy

11. **055** — reliability and autonomy umbrella (do not run directly)
12. **055a** — harness contract freeze
13. **055b** — task-family classifier, prompt compiler, and split strategy
14. **055c** — seam manifest and semantic contract validator
15. **056** — failure classifier and remediation planner
16. **057** — localized repair and failure artifacts
17. **058** — backlog readiness and state engine
18. **059** — CI / PR / merge controller
19. **060** — autonomy loop integration
20. **061** — continuation reset and numbering sync

### Deferred continuation after reliability tranche

21. **062** — integrated capability E2E flow
22. **063** — failure-journal live seam
23. **064** — safe-parallelism / review integration
24. **065** — runtime artifact quarantine integration
25. **066** — package extraction prep
26. **067** — canonical docs path policy
27. **068** — task scope / split heuristics follow-on

## Exit criteria for 055–061

- stable harness contract frozen with regression coverage
- task families recognized and routed deliberately
- lane-specific prompt compilation exists
- seam manifests / semantic contract validation are in place for seam-heavy tasks
- failure classes map to remediation strategies
- localized repair and failure artifacts are deterministic
- backlog readiness/next-task state becomes explicit
- PR/CI/merge becomes part of the orchestrator’s control loop
- the controller can self-heal through at least one recoverable failure without human intervention
- docs/tasks/numbering are re-aligned so the deferred continuation resumes cleanly

## Repo strategy note

Standalone extraction remains recommended later, after both the reliability/autonomy tranche and the deferred continuation complete.
