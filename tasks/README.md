# Tasks README

Current completed reliability tranche

- 157 — orchestrator benchmark scorecard integration
- 158 — orchestrator empty bundle transport retry and classifier
- 159 — orchestrator runtime artifact quarantine and subset preservation normalization
- 160 — orchestrator completion integrity gate
- 161 — orchestrator one-task reliability minipack re-proof
- 162 — orchestrator authority-gate evidence narrowing
- 163 — orchestrator deliverable contract and completion prompt hardening
- 164 — orchestrator runtime artifact hygiene and typo normalization
- 165 — orchestrator one-task reliability minipack re-proof v2

Next sequential tranche

- 166 — orchestrator strict no-manual-intervention scorecard
- 167 — orchestrator authority corroboration and run truth
- 168 — orchestrator top failure family elimination tranche
- 169 — orchestrator one-task promotion re-proof
- 170 — orchestrator default single-task path and two-task pilot gate

Task-number cleanup note

The repo accumulated duplicate planning files during the 157–165 reliability sprints. The completed task numbers above are the canonical completed sequence. Legacy duplicate task files that were not actually executed should be removed or renumbered out of the way before continuing.

Working mode

- Keep the project in one-task reliability mode until the promotion re-proof says otherwise.
- Default to orchestrator-run mode for curated one-task tasks when the runtime is stable enough.
- Use small manual engine fixes only when the runtime itself is the blocker.
- Treat any mid-run human file edit during a benchmark run as a failed autonomous attempt.
- Do not widen to multi-task execution until promotion and the explicit two-task pilot gate justify it.
