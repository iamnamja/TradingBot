# Orchestrator Controls and Policies

## Runtime Artifact Quarantine Policy

The task runner shell quarantines known safe runtime artifacts before final commit/push.
This policy is implemented in `agents.lib.artifact_quarantine` and consumed by the
run-task shell via `_cleanup_runtime_artifacts_for_commit(...)`.

### Known safe artifacts

- `last_output.txt`
- `_last_agent_model_output.txt`
- `_last_agent_file_bundle.txt`

### Required behavior

- Known safe artifacts are auto-unstaged (`git rm --cached --ignore-unmatch`) and deleted when present.
- Quarantined artifacts remain visible in returned classification/warning/audit data.
- Unknown runtime artifacts are never silently ignored and must continue to block according to policy.
- Delegation boundary: `agents/run_task.py` should delegate quarantine policy to
  `agents.lib.artifact_quarantine.quarantine_runtime_artifacts(...)`.

### Guardrails

- Do not weaken merge/approval policy due to artifact handling.
- Do not silently permit unknown artifact names.
- Keep CLI/task shell behavior unchanged; quarantine is a thin policy extraction.
