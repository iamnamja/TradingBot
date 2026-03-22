# Orchestrator Roadmap (Tasks 049–054)

## Context

Tasks 042–048 completed the main productization capability tranche.

The next phase is about making the orchestrator **stable enough to reuse across projects without depending on TradingBot-specific history or shell quirks**.

## Tranche goals

- converge `agents/run_task.py` into a truly thin shell
- freeze the public orchestrator surface
- normalize stale status/docs surfaces
- prove portability with a second project fixture
- add integrated end-to-end scenarios across 043–048
- prepare eventual extraction into its own package/repository

## Task summary

| Task | Name | Goal |
|------|------|------|
| 049 | Run Task Shell Convergence | remove duplicate shell/export definitions and finish thin-shell routing |
| 050 | Public Interface Freeze | freeze config / adapter / validator / task-spec public surfaces |
| 051 | Docs / Status Normalization | update docs to match the real post-048 baseline |
| 052 | Second Project Portability Proof | prove the orchestrator against a non-TradingBot fixture project |
| 053 | Integrated Capability Scenarios | test 043–048 together in realistic orchestrator flows |
| 054 | Package Extraction Prep | prepare the orchestrator for clean later extraction |

## Recommended order

1. 049a — export/wrapper dedupe
2. 049b — final shell routing extraction
3. 050 — public interface freeze
4. 051 — docs normalization
5. 052 — second-project proof
6. 053 — integrated scenarios
7. 054 — package extraction prep

## Exit criteria for the tranche

The orchestrator is ready for packaging / repo extraction when:

- `agents/run_task.py` is thin and stable
- there is one stable definition per public shell wrapper/export seam
- public config / adapter / validator / task-spec surfaces are documented and frozen
- a second project fixture passes through bootstrap + validation paths
- integrated scenarios cover runtime artifacts, spec mode, failure journaling, validators, and safe parallelism together
- docs accurately reflect the implementation baseline
