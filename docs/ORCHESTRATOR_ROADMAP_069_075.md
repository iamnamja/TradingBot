# Orchestrator Roadmap 069–075

## Purpose

This roadmap covers the backlog-execution continuation after the protected/controller stabilization work.

## Sequence

1. **069** — controller decomposition second extraction  
   Extract protected-lane and duplicate-bundle-repair helpers out of `agents/run_task.py` while preserving helper compatibility.

2. **070** — task-list manifest and queue model  
   Add a narrow manifest format plus deterministic queue construction with validation and duplicate handling.

3. **070a** — exact deliverable parser and completion gate hardening  
   Broaden exact-deliverable parsing to the current task contract styles and fail closed when required deliverables are omitted.

4. **070b** — runtime artifact retention and visibility  
   Preserve runtime artifact quarantine as the default pushed-run behavior, while adding clearer retention/quarantine lifecycle handling for known-safe `_last_agent_*` artifacts.

5. **071** — batch state persistence and resume  
   Persist queue/batch execution state and allow deterministic resume behavior.

6. **071a** — user-facing runtime artifact retention switch  
   Surface the internal known-safe artifact retention path through an explicit CLI flag and environment variable so operators can intentionally keep `_last_agent_model_output.txt` and `_last_agent_file_bundle.txt` after successful pushed runs.

7. **072** — per-task checkpoint and branch isolation  
   Add safer task-level checkpointing and isolation boundaries for backlog execution.

8. **073** — batch failure policy and continue gate  
   Make post-task continue/stop/manual policy explicit and machine-readable.

9. **074** — batch runner CLI and summary artifacts  
   Add a user-facing batch runner entry point and stable batch summary outputs.

10. **075** — backlog execution end-to-end proof  
    Validate the backlog-runner flow across multiple tasks under the current contracts.

## Current guidance

- Treat controller/protected tasks with higher scrutiny than additive queue/state tasks.
- Enforce exact deliverable completeness from real branch diffs.
- Keep backlog execution conservative: explicit state, resume, isolation, and policy should land before broader autonomous batching claims.
