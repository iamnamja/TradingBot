# TradingBot / Orchestrator Project State

## TradingBot

- still at manual paper-trading readiness
- app-level backlog is intentionally paused behind orchestrator reliability work

## Orchestrator

### Completed on `main`

- 042–048 hardening tranche
- 049–052 shell/public-interface/docs/portability tranche
- 053 stable seam registry
- 054a–054b meta harness lane gate + bundle preflight/localized repair

### Active next tranche

The orchestrator is now on a **Reliability / Recovery / Autonomy** trajectory.

The controller must become good at:

- choosing the right lane for a task family
- compiling a better request for that lane
- validating seam contracts semantically
- classifying failures into repair, retry, split, defer, or escalation
- preserving good outputs and repairing only the bad subset
- deciding what task is ready next
- controlling PR/CI/merge as part of the same loop

### Deferred continuation

The earlier integration/seam-family continuation remains deferred until the reliability tranche lands.
