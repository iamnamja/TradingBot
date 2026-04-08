from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

DEFAULT_SINGLE_TASK_LEDGER_PATH = "artifacts/autonomous_single_task/run_ledger.jsonl"
LEDGER_SCHEMA_VERSION = 1
ITERATION_RE = re.compile(r"=== Iteration\s+(\d+)/(\d+)\s+===")


def default_single_task_ledger_path() -> str:
    return DEFAULT_SINGLE_TASK_LEDGER_PATH


def _tail_text(text: str, *, limit: int = 1200) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    return value[-limit:]


def _default_executor(command: Sequence[str]) -> dict[str, object]:
    completed = subprocess.run(list(command), text=True, capture_output=True)
    return {
        "command": list(command),
        "returncode": int(completed.returncode),
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def summarize_single_task_execution(*, execution_result: Mapping[str, object] | None = None) -> dict[str, object]:
    result = dict(execution_result or {})
    stdout = str(result.get("stdout", "") or "")
    stderr = str(result.get("stderr", "") or "")
    combined = f"{stdout}\n{stderr}"
    lower = combined.lower()
    iterations = [(int(current), int(total)) for current, total in ITERATION_RE.findall(combined)]
    observed_iterations = max((current for current, _total in iterations), default=0)
    configured_max_iters = max((total for _current, total in iterations), default=0)
    retry_count = max(0, observed_iterations - 1)
    return {
        "command": list(result.get("command", []) or []),
        "returncode": int(result.get("returncode", 0) or 0),
        "observed_iterations": observed_iterations,
        "configured_max_iters": configured_max_iters,
        "retry_count_observed": retry_count,
        "missing_deliverable_retry_observed": "missing deliverable" in lower,
        "coupled_compatibility_repair_observed": "compatibility surface" in lower or "compatibility-surface" in lower,
        "last_green_subset_preserved_observed": "last-known-good subset" in lower or "last green subset" in lower,
        "all_checks_passed_observed": "all checks passed!" in lower,
        "pytest_green_observed": "[100%]" in combined and "failed" not in lower,
        "ruff_green_observed": "all checks passed!" in lower,
        "no_checks_reported_observed": "no checks reported on the" in lower,
        "stdout_tail": _tail_text(stdout),
        "stderr_tail": _tail_text(stderr),
    }


def canonical_single_task_run_ledger_entry(
    *,
    task_path: str,
    task_text: str,
    required_paths: Sequence[str],
    admission: Mapping[str, object],
    proof_admission: Mapping[str, object],
    execution_summary: Mapping[str, object] | None,
    started_at: str,
    completed_at: str,
    ledger_path: str,
    push_requested: bool,
    keep_runtime_artifacts: bool,
) -> dict[str, object]:
    admission_dict = dict(admission)
    proof_dict = dict(proof_admission)
    execution = dict(execution_summary or {})
    allowed = bool(admission_dict.get("autonomous_single_task_allowed", False)) and bool(
        proof_dict.get("proof_task_admission_allowed", False)
    )
    lane = str(admission_dict.get("autonomous_single_task_lane", "") or "")
    proof_required = bool(proof_dict.get("proof_task_admission_required", False))
    execution_invoked = bool(execution)
    returncode = int(execution.get("returncode", 0) or 0) if execution_invoked else None

    if not allowed and lane == "escalation_required":
        final_decision = "escalation_required"
        escalation_required = True
        escalation_reason = str(admission_dict.get("autonomous_single_task_rationale", "") or "")
    elif not allowed:
        final_decision = "blocked_supervised_only"
        escalation_required = False
        escalation_reason = str(
            proof_dict.get("proof_task_admission_reason")
            or admission_dict.get("autonomous_single_task_rationale")
            or "Task was not admitted to the safe autonomous single-task lane."
        )
    elif returncode == 0:
        final_decision = "completed"
        escalation_required = False
        escalation_reason = ""
    else:
        final_decision = "execution_failed"
        escalation_required = True
        escalation_reason = "Admitted single-task run failed and should be handed back to supervised recovery."

    return {
        "schema_version": LEDGER_SCHEMA_VERSION,
        "runner": "autonomous_single_task",
        "task_path": str(task_path),
        "task_name": Path(task_path).name,
        "started_at": started_at,
        "completed_at": completed_at,
        "ledger_path": str(ledger_path),
        "push_requested": bool(push_requested),
        "keep_runtime_artifacts": bool(keep_runtime_artifacts),
        "required_paths": [str(path) for path in required_paths],
        "admission": {
            "autonomous_single_task_lane": lane,
            "autonomous_single_task_allowed": bool(admission_dict.get("autonomous_single_task_allowed", False)),
            "autonomous_single_task_rationale": str(admission_dict.get("autonomous_single_task_rationale", "") or ""),
            "task_family_allowlisted": bool(admission_dict.get("task_family_allowlisted", False)),
            "autonomy_allowlist_family": str(admission_dict.get("autonomy_allowlist_family", "") or ""),
            "self_hosting_control_plane_task": bool(admission_dict.get("self_hosting_control_plane_task", False)),
            "self_hosting_control_plane_required_paths": list(admission_dict.get("self_hosting_control_plane_required_paths", []) or []),
            "proof_task_detected": bool(proof_dict.get("proof_task_detected", False)),
            "proof_task_admission_required": proof_required,
            "proof_task_admission_allowed": bool(proof_dict.get("proof_task_admission_allowed", False)),
            "proof_task_admission_reason": str(proof_dict.get("proof_task_admission_reason", "") or ""),
        },
        "retry": {
            "observed_iterations": int(execution.get("observed_iterations", 0) or 0),
            "configured_max_iters": int(execution.get("configured_max_iters", 0) or 0),
            "retry_count_observed": int(execution.get("retry_count_observed", 0) or 0),
            "missing_deliverable_retry_observed": bool(execution.get("missing_deliverable_retry_observed", False)),
            "coupled_compatibility_repair_observed": bool(execution.get("coupled_compatibility_repair_observed", False)),
            "last_green_subset_preserved_observed": bool(execution.get("last_green_subset_preserved_observed", False)),
        },
        "validation": {
            "execution_invoked": execution_invoked,
            "returncode": returncode,
            "all_checks_passed_observed": bool(execution.get("all_checks_passed_observed", False)),
            "pytest_green_observed": bool(execution.get("pytest_green_observed", False)),
            "ruff_green_observed": bool(execution.get("ruff_green_observed", False)),
            "no_checks_reported_observed": bool(execution.get("no_checks_reported_observed", False)),
        },
        "escalation": {
            "required": escalation_required,
            "reason": escalation_reason,
        },
        "final_decision": final_decision,
        "execution": {
            "command": list(execution.get("command", []) or []),
            "stdout_tail": str(execution.get("stdout_tail", "") or ""),
            "stderr_tail": str(execution.get("stderr_tail", "") or ""),
        },
        "task_excerpt": _tail_text(task_text, limit=400),
    }


def append_single_task_run_ledger_entry(entry: Mapping[str, object], *, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path or entry.get("ledger_path") or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(entry), sort_keys=True) + "\n")
    return path.as_posix()


def _build_run_task_command(
    *,
    task_path: str,
    provider: str | None,
    model: str | None,
    max_iters: int,
    push: bool,
    keep_runtime_artifacts: bool,
) -> list[str]:
    command = [sys.executable, "-m", "agents.run_task", task_path, "--max-iters", str(max_iters)]
    if provider:
        command.extend(["--provider", provider])
    if model:
        command.extend(["--model", model])
    if push:
        command.append("--push")
    if keep_runtime_artifacts:
        command.append("--keep-runtime-artifacts")
    return command


def run_autonomous_single_task(
    task_path: str,
    *,
    provider: str | None = None,
    model: str | None = None,
    max_iters: int = 4,
    push: bool = False,
    keep_runtime_artifacts: bool = False,
    ledger_path: str | Path | None = None,
    now: Callable[[], str] | None = None,
    executor: Callable[[Sequence[str]], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    import agents.run_task as run_task

    ledger_location = str(ledger_path or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    task_file = Path(task_path)
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")
    task_text = task_file.read_text(encoding="utf-8", errors="replace")
    required_paths = list(run_task.parse_required_files(task_text))
    admission = dict(
        run_task.evaluate_autonomous_single_task_admission(
            required_paths,
            task_file=task_file.as_posix(),
            task_text=task_text,
        )
    )
    proof_admission = dict(
        run_task.evaluate_proof_task_admission(
            task_text=task_text,
            task_file=task_file.as_posix(),
            required_paths=required_paths,
        )
    )

    clock = now or (lambda: "")
    started_at = str(clock() or "")
    execution_summary: dict[str, object] | None = None
    allowed = bool(admission.get("autonomous_single_task_allowed", False)) and bool(
        proof_admission.get("proof_task_admission_allowed", False)
    )
    if allowed:
        command = _build_run_task_command(
            task_path=task_file.as_posix(),
            provider=provider,
            model=model,
            max_iters=max_iters,
            push=push,
            keep_runtime_artifacts=keep_runtime_artifacts,
        )
        raw_execution = dict((executor or _default_executor)(command))
        execution_summary = summarize_single_task_execution(execution_result=raw_execution)
    completed_at = str(clock() or started_at)
    entry = canonical_single_task_run_ledger_entry(
        task_path=task_file.as_posix(),
        task_text=task_text,
        required_paths=required_paths,
        admission=admission,
        proof_admission=proof_admission,
        execution_summary=execution_summary,
        started_at=started_at,
        completed_at=completed_at,
        ledger_path=ledger_location,
        push_requested=push,
        keep_runtime_artifacts=keep_runtime_artifacts,
    )
    persisted_path = append_single_task_run_ledger_entry(entry, ledger_path=ledger_location)
    return {
        "task_path": task_file.as_posix(),
        "ledger_path": persisted_path,
        "entry": entry,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("task", help="Path to a single task markdown file")
    ap.add_argument("--provider", default=None, choices=["openai", "anthropic"])
    ap.add_argument("--model", default=None)
    ap.add_argument("--max-iters", type=int, default=4)
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--keep-runtime-artifacts", action="store_true")
    ap.add_argument("--ledger-path", default=DEFAULT_SINGLE_TASK_LEDGER_PATH)
    args = ap.parse_args()

    result = run_autonomous_single_task(
        args.task,
        provider=args.provider,
        model=args.model,
        max_iters=args.max_iters,
        push=args.push,
        keep_runtime_artifacts=args.keep_runtime_artifacts,
        ledger_path=args.ledger_path,
    )
    entry = dict(result["entry"])
    print(json.dumps(entry, indent=2, sort_keys=True))
    decision = str(entry.get("final_decision", "") or "")
    if decision == "completed":
        return 0
    if decision in {"blocked_supervised_only", "escalation_required"}:
        return 2
    validation = dict(entry.get("validation", {}) or {})
    return int(validation.get("returncode", 1) or 1)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
