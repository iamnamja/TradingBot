# Tasks README

Current sequential reliability tranche

- 157 — orchestrator benchmark scorecard integration
- 158 — orchestrator empty bundle transport retry and classifier
- 159 — orchestrator runtime artifact quarantine and subset preservation normalization
- 160 — orchestrator completion integrity gate
- 161 — orchestrator one-task reliability minipack re-proof

Next reliability tranche

- 162 — orchestrator authority-gate evidence narrowing
- 163 — orchestrator deliverable contract and completion prompt hardening
- 164 — orchestrator runtime artifact hygiene and typo normalization
- 165 — orchestrator one-task reliability minipack re-proof v2

Working mode

- Default to orchestrator-run mode for curated one-task tasks when the runtime is stable enough.
- Use small manual engine fixes only when the runtime itself is the blocker.
- Treat any mid-run human file edit during a benchmark run as a failed autonomous attempt.
- Do not widen to multi-task execution until re-proof results justify it.
