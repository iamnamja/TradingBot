# Orchestrator Roadmap 162-165

This roadmap is the second one-task reliability sprint.

Objective

Keep the project in one-task reliability mode and remove the blocker families surfaced by the first minipack re-proof:
- authority-gate friction
- incomplete deliverable wiring
- runtime artifact hygiene noise

Tasks

## 162 — authority-gate evidence narrowing
Narrow the evidence taxonomy for authority blocks so the runner only hard-blocks when the evidence is explicit enough.

## 163 — deliverable contract and completion prompt hardening
Make proof-task contracts and completion-integrity feedback more explicit so partial/helper-only implementations are less likely to recur.

## 164 — runtime artifact hygiene and typo normalization
Normalize runtime artifact naming and retention so proof-mode diagnostics are clear and predictable.

## 165 — one-task reliability minipack re-proof v2
Re-run the reliability minipack and record whether the second sprint improved the lane enough to continue staged orchestrator-run mode confidently.

Exit criteria for this sprint

- proof-mode runs no longer fail on avoidable artifact/path confusion
- authority blocks are narrower and more explicit
- completion-integrity failures provide clearer repair guidance
- the second re-proof gives a stronger reliability signal than the first
