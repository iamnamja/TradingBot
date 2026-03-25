# Orchestrator Controls and Policies

## Purpose

This document defines the practical controls and policy posture for the orchestrator as of the post-052 baseline, with the 053–061 continuation next.

## Status baseline

- Tranche **042–048 is complete**
- Tasks **049–052 are complete**
- Tasks **053–061 are the current hardening / integration continuation**
- The orchestrator is reusable and increasingly productized, but remains in-repo for now

## Core control layers

1. **Task-contract discipline**
   - Structured task specs and machine-parseable directives
   - Explicit deliverables and guardrails
2. **Protected-file policy enforcement**
   - Append-before / exact-copy / forbid semantics
   - Controlled method insertion and semantic preflight pathways
3. **Execution safety**
   - Dry-run and simulation support
   - Runtime artifact quarantine and failure journaling
4. **Review and approval gates**
   - Compliance checks, review result handling, and explicit approval checkpoints
5. **Repository integrity**
   - Branch/worktree guardrails, merge workflow controls, and audit traces
6. **Recovery and resumability**
   - Persistent state, restart/resume paths, and retry-aware behavior
7. **Parallelism controls**
   - Safe parallel execution constraints
8. **Stable seam governance**
   - Explicit test seams, seam-aware preflight, and controlled integrated coverage expansion

## Policy posture by sequence

### Completed baseline: 042–048

- Harness modularization and extraction boundaries stabilized
- Runtime foundations/parsers/semantic preflight extraction complete
- Thin run-task shell parity achieved
- Artifact quarantine, spec two-phase execution, frozen-task handling, failure journal, bootstrap adapter, validator plugins, and safe parallelism completed

### Completed stabilization: 049–052

- run-task shell convergence and routing dedupe
- public interface freeze reinforcement
- docs/status normalization
- second-project portability proof

### Active continuation: 053–061

Focus:

- stable seam registry for integration tests
- task / seam preflight linting
- one seam-aligned integrated capability flow
- focused seam-family hardening (failure journal, review, quarantine)
- package extraction preparation
- canonical docs path policy
- task scope / split heuristics

## Repository separation policy

- **Current policy**: keep orchestrator in this repository while the 053–061 continuation is completed
- **Recommended next policy**: separate into its own repo/package **after** 053–061 readiness criteria are met

## Non-goals (current phase)

- No claim that orchestrator has already been extracted
- No replacement of safety-first controls with permissive defaults
- No collapse of approval/review/audit checkpoints
- No broad integrated tests that redefine optional seams without prior seam stabilization

## Relationship to TradingBot

The orchestrator advances engineering reliability and portability; TradingBot remains focused on manual paper-trading readiness. Orchestrator productization progress does not imply TradingBot production autonomy.
