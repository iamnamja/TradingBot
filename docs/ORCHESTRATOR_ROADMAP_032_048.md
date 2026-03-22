# Orchestrator Roadmap (Tasks 032–048)

## Context

Tasks 032–048 are now complete in substance on `main`.

This tranche took the orchestrator from a strong internal harness to a materially more reusable delivery product.

## Completed roadmap summary

| Task | Name | Status |
|------|------|--------|
| 032 | Execution Result Normalization | ✅ |
| 033 | Real Review and Compliance Gate | ✅ |
| 034 | Branch and Worktree Guardrails | ✅ |
| 035 | PR Creation Workflow | ✅ |
| 036 | Resume After Approval | ✅ |
| 037 | Persistent Backlog State | ✅ |
| 038 | Run Loop / CLI / Decision Logging | ✅ |
| 039 | Harness Hardening Tranche | ✅ |
| 040 | End-to-End Integration Harness | ✅ |
| 041 | Multi-Project Hardening | ✅ |
| 042a–042d | Harness Modularization | ✅ |
| 043 | Runtime Artifact Quarantine | ✅ |
| 044a–044b | Spec / Execution Two-Phase Workflow | ✅ |
| 045 | Structured Failure Journal | ✅ |
| 046 | Project Bootstrap Adapter | ✅ |
| 047 | Verification Plugins / Validators | ✅ |
| 048 | Safe Parallelism | ✅ |

## What 042–048 accomplished

- moved substantial shell logic out of `agents/run_task.py` into `agents/lib/*`
- added runtime artifact quarantine
- separated spec capture from execution
- added structured failure journaling
- added project bootstrap support
- added config/adapter-driven validator plugins
- added engine-side safe parallelism controls

## Lessons from the tranche

- shell-sensitive work sometimes required curated direct patches instead of repeated blind reruns
- preserving compatibility seams in `agents/run_task.py` is as important as moving logic out of it
- validator plugins must preserve legacy built-in `ruff` / `pytest` behavior where tests depend on it
- safe parallelism must be layered onto the real runner surface rather than replace it
- docs/status surfaces quickly become stale when the implementation moves faster than the markdown

## Remaining structural gap after 048

The main remaining gap is **shell convergence**:

- `agents/run_task.py` is still too large
- duplicate wrapper/export definitions still exist
- the public shell surface is not frozen yet
- portability has not yet been proven with a second client project

## Transition

The next roadmap is now **Tasks 049–054**, focused on stabilization, portability proof, and package extraction prep.
