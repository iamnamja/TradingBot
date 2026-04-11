# TRADINGBOT project state

This project contains a multi-purpose orchestrator and a simulated trading bot target. The orchestrator executes single-task and batch workflows with strict contracts, including:

- exact deliverable declarations in task specs
- authority gates and CI surface integration
- semantic preflight, protected method edits, and runtime artifact quarantine

New in the latest evolution:
- Completion-integrity now depends on both the explicit task deliverable contract and the follow-up repair prompt. The gate remains mechanical: it parses the “Create or update these exact files” list and enforces required existing-surface touches when the task calls for wiring into the existing live surface. If a bundle is rejected for helper-only or new-surface-only changes, the runner appends a clearer, contract-driven repair prompt that enumerates the exact required files and the differences observed in the submitted bundle.

The trading bot surfaces (brokers, data, strategy, execution, risk) remain stable and covered by compatibility tests. The orchestrator continues to prefer deterministic behaviors and safe defaults across all modules.
