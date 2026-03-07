# TradingBot and Orchestrator Relationship

## Two products in one repository
This repository now contains two related but distinct products:

### 1. TradingBot
A safe, testable algorithmic trading bot with paper-trading readiness.

### 2. Orchestrator
A reusable software-delivery engine that can build and evolve TradingBot and future software projects through a task-driven workflow.

## Why this matters
The orchestrator must not be tightly coupled to TradingBot. TradingBot is the first project adapter and testbed, not the permanent center of the orchestration engine.

## Current TradingBot status
TradingBot currently includes:
- core bot pipeline through Task 010
- paper-trading readiness through Task 014

## Current orchestrator status
The orchestrator currently includes:
- backlog/state tracking
- review/compliance checking
- failure classification
- PR/CI/merge management
- repair workflow
- generic project adapter foundation

## Next orchestrator milestone
The next milestone is to make the orchestrator fully operational and portable through:
- real loop runner
- decision audit/journal
- resume/recovery
- policy engine
- multi-project adapter examples
- dry-run simulation

## Long-term intent
In the future, the orchestrator should be able to:
- continue building TradingBot
- bootstrap future software projects
- reuse the same core engine with different adapters and policies
