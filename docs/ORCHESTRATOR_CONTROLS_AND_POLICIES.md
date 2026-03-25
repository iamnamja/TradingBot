# Orchestrator Controls and Policies

## Purpose

This document defines the practical controls and policy posture for the orchestrator as of the post-048 baseline, with the 049–054 stabilization tranche next.

## Status baseline

- Tranche **042–048 is complete**.
- Tranche **049–054 is the current stabilization sequence**.
- The orchestrator is reusable and increasingly productized, but remains in-repo for now.

## Core control layers

1. **Task-contract discipline**
   - Structured task specs and machine-parseable directives.
   - Explicit deliverables and guardrails.
2. **Protected-file policy enforcement**
   - Append-before / exact-copy / forbid semantics.
   - Controlled method insertion and semantic preflight pathways.
3. **Execution safety**
   - Dry-run and simulation support.
   - Runtime artifact quarantine and failure journaling.
4. **Review and approval gates**
   - Compliance checks, review result handling, and explicit approval checkpoints.
5. **Repository integrity**
   - Branch/worktree guardrails, merge workflow controls, and audit traces.
6. **Recovery and resumability**
   - Persistent state, restart/resume paths, and retry-aware behavior.
7. **Parallelism controls**
   - Safe parallel execution constraints (completed in 048).

## Policy posture by tranche

### Completed: 042–048

- Harness modularization and extraction boundaries stabilized.
- Runtime foundations/parsers/semantic preflight extraction complete.
- Thin run-task shell parity achieved.
- Artifact quarantine, spec two-phase execution, frozen-task handling, failure journal, bootstrap adapter, validator plugins, and safe parallelism completed.

### Active stabilization tranche: 049–054

Focus:

- run-task shell convergence and routing dedupe
- public interface freeze reinforcement
- docs/status normalization
- second-project portability proof
- integrated capabilities end-to-end proving
- package extraction preparation (without immediate extraction)

## Repository separation policy

- **Current policy**: keep orchestrator in this repository while stabilization tranche 049–054 is completed.
- **Recommended next policy**: separate into its own repo/package **after** 049–054 readiness criteria are met.

## Non-goals (current phase)

- No claim that orchestrator has already been extracted.
- No replacement of safety-first controls with permissive defaults.
- No collapse of approval/review/audit checkpoints.

## Relationship to TradingBot

The orchestrator advances engineering reliability and portability; TradingBot remains focused on manual paper-trading readiness. Orchestrator productization progress does not imply TradingBot production autonomy.
