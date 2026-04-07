# Orchestrator Roadmap — Multi-Project Portfolio Autonomy Continuation (116–123)

## Where this continuation starts

Task 115 completed a bounded supervised local-first ordinary-manifest re-proof.

That is a meaningful milestone, but it is still not the same thing as a durable orchestrator that can pick work across multiple projects, isolate execution safely, self-heal with stronger repair logic, and determine what should happen next with less babysitting.

The next tranche should therefore focus on turning the current bounded ordinary-manifest proof into the first credible **multi-project portfolio operating mode**.

## Main gaps this tranche addresses

- the orchestrator still behaves more like a single-repo proof harness than a portfolio-aware control plane
- project portability exists, but there is not yet one canonical project registry and per-project contract surface
- state, branch, workspace, and carry-forward memory are not yet isolated strongly enough for multiple concurrent or rotating projects
- next-task selection is still too static and manifest-shaped instead of being driven by backlog readiness, priority, and dependency truth
- decomposition is still bounded but not yet informed by an explicit dependency graph
- self-heal can stop repeated no-progress retries, but it still lacks repair-plan ranking and rollback-to-last-green behavior
- project-specific validation and authority contracts are still too repo-shaped for broader portability
- hosted authority is still truthful but not yet operationally converged enough for low-babysitting portfolio use

## Planned order

### 116 — Project registry and per-project contract
Add a canonical project registry so the orchestrator can describe each project by id, repo root, workspace type, validation contract, branch policy, and autonomy lane without hard-coding monorepo assumptions.

### 117 — Project-scoped state, branch, and workspace isolation
Split batch state, checkpoints, branch naming, workspace state, and carry-forward memory by project so multiple projects cannot bleed state into each other.

### 118 — Backlog intake and next-task selection policy
Teach the controller how to choose the next task from a backlog using explicit priority, readiness, dependency, and blocked-state rules instead of only manifest order.

### 119 — Dependency graph and decomposition planner
Add an explicit dependency graph and bounded decomposition planner so larger work can be split and scheduled honestly rather than treated as flat backlog entries.

### 120 — Repair planner ranking and rollback-to-last-green
Strengthen self-heal by ranking repair plans, recording last-green validation truth, and allowing bounded rollback before attempting broader repairs.

### 121 — Project-aware validation matrix and authority profiles
Build project-specific validation plans and authority profiles from the registry so each project can declare its own focused checks, full checks, bootstrap requirements, and merge evidence.

### 122 — Hosted authority convergence and merge eligibility proof
Move the hosted-authority story from truthful probe status toward operational merge-eligibility truth that is grounded in real branch protection and required-check behavior.

### 123 — Supervised multi-project portfolio scheduler re-proof
Re-prove the orchestrator over a bounded portfolio slice spanning more than one project, with project selection, isolated state, next-task choice, and conservative stop behavior.

## Expected lane mix

- **Manual first:** 116, 117, 118, 119, 120
- **Manual or hybrid:** 121, 122
- **Best orchestrator-supervised candidate after those land:** 123

## Success criteria for this roadmap

This roadmap is successful when:

- projects are described through one canonical registry and contract surface
- state, branches, workspaces, and memory are isolated by project
- the controller can choose the next task using explicit backlog policy instead of only manifest order
- larger work can be decomposed through a bounded dependency-aware planner
- self-heal can rank repair options and roll back to the last green state when needed
- validation and authority are project-aware instead of monorepo-shaped
- the orchestrator can progress through a bounded multi-project portfolio slice with less babysitting than today
