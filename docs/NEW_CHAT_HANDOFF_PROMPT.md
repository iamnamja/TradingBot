# New Chat Handoff Prompt

We are continuing work on the TradingBot orchestrator project.

Use the attached current `agents`, `docs`, `tasks`, `tests`, `README.md`, and `requirements.txt` snapshots as the source of truth.

## Current completed state

- reliability/autonomy continuation complete through 067
- stabilization and backlog foundations complete through 075
- autonomy/controller-thinning tranche complete through 082
- recent key milestones:
  - 076 final acceptance reviewer/report
  - 077 targeted acceptance self-heal
  - 078 canonical batch executor loop
  - 079 accepted-task PR/check/merge/reset gate
  - 080 resume semantics
  - 081 controller decomposition extraction
  - 082 first narrow autonomous ordinary-manifest proof

## Important reality

- short ordinary-manifest proof now exists, but 082 exposed remaining controller-contract and repair-discipline gaps
- broad arbitrary protected/controller manifest autonomy is still not an honest claim
- `agents/run_task.py` is thinner than before, but controller glue still exists and should keep moving outward carefully

## Next intended tranche

- 083 controller contract canonicalization
- 084 non-reexecuting retry/self-heal channel
- 085 merge-posture truth persistence and resume contract
- 086 semantic failure digest and controller repair context
- 087 controller-task strict mode and patch-quality gate
- 088 controller decomposition fourth extraction
- 089 hardened autonomous short-manifest proof

## Working style

- use `tasks/README.md` as canonical task ordering
- exact deliverable completeness matters
- compare actual committed diff vs task-required files
- run `ruff check .` and `pytest -q` before considering a task done
- for controller-core tasks, manual patches are often still appropriate
- docs should not claim a proof/milestone before final acceptance actually passes
- prefer targeted cleanup patches over blind reruns once a branch is close

## Immediate next move

Treat **083** as a manual patch first. It is the contract-stabilization task that the rest of 084–089 depends on.
