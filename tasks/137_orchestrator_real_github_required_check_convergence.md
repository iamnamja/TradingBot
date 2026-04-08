# Task 137 — Orchestrator real GitHub required-check convergence

## Goal
Close the gap between modeled hosted-authority truth and the repo’s real GitHub branch-protection / required-check enforcement so unattended-readiness claims can become operationally honest.

## Scope
- GitHub required-check context discovery and stable `ci-required` contract
- branch-protection / required-check setup verification
- operational blocking evidence when checks are absent, weak, or not actually enforced

## Create or update these exact files
- `agents/lib/git_workflow.py`
- `agents/lib/project_registry.py`
- `agents/run_task.py`
- `tests/test_merge_manager_integration.py`
- `tests/test_project_registry.py`
- `tests/test_run_task_runtime_foundations.py`
- `docs/ORCHESTRATOR_GITHUB_REQUIRED_CHECK_SETUP.md`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `docs/ORCHESTRATOR_PRODUCT_SPEC.md`
- `docs/README.md`

## Required behavior
The implementation should verify the real GitHub required-check / branch-protection posture around the stable `ci-required` context, surface whether the repo is truly unattended-ready, and keep `no checks reported` or equivalent weak-evidence states explicitly blocking. The work should stay bounded to operational convergence and must not widen autonomy claims.

## Acceptance
This task is complete when the runtime/reporting surfaces make real GitHub enforcement convergence explicit, focused tests cover converged and non-converged states, and the docs remain narrowly truthful about unattended-readiness.
