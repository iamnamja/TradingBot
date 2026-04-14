# TradingBot + Orchestrator Monorepo

## Next continuation target

Stay conservative while fixing recurring contract drift and model-transport mismatch before any new capability widening:

- eliminate repeated README/project-state headline drift with an explicit docs-status consistency guard
- define explicit model profiles and output-transport contracts instead of assuming one file-bundle mode for every model
- split Codex transport work into a normal-lane parser/apply step (188a) and a protected runner-integration step (188b)
- add provider/model capability negotiation and safe fallback or explicit diagnostics when a selected model cannot satisfy the task transport contract
- record a post-transport checkpoint before resuming any cautious bounded capability widening
