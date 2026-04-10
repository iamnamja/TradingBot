from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Callable, Mapping, Sequence

DEFAULT_SINGLE_TASK_LEDGER_PATH = "artifacts/autonomous_single_task/run_ledger.jsonl"
DEFAULT_SINGLE_TASK_CANARY_METRICS_PATH = "artifacts/autonomous_single_task/canary_metrics.json"
DEFAULT_SINGLE_TASK_RECOVERY_REPORT_PATH = "artifacts/autonomous_single_task/recovery_report.json"
DEFAULT_SINGLE_TASK_SUPERVISED_HANDOFF_PATH = "artifacts/autonomous_single_task/supervised_handoff.json"
DEFAULT_SINGLE_TASK_RESUME_STATE_PATH = "artifacts/autonomous_single_task/resume_state.json"
DEFAULT_SCHEDULER_SAFE_LANE_POLICY_PATH = "artifacts/autonomous_single_task/scheduler_safe_lane_policy.json"
DEFAULT_OPERATOR_PROOF_BUNDLE_PATH = "artifacts/autonomous_single_task/operator_proof_bundle.json"
LEDGER_SCHEMA_VERSION = 1
CANARY_METRICS_SCHEMA_VERSION = 1
SUPERVISED_HANDOFF_SCHEMA_VERSION = 1
OPERATOR_PROOF_BUNDLE_SCHEMA_VERSION = 1
ITERATION_RE = re.compile(r"=== Iteration\s+(\d+)/(\d+)\s+===")


def default_single_task_ledger_path() -> str:
    return DEFAULT_SINGLE_TASK_LEDGER_PATH


def default_single_task_canary_metrics_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("canary_metrics.json").as_posix()


def default_single_task_recovery_report_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("recovery_report.json").as_posix()


def default_single_task_supervised_handoff_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("supervised_handoff.json").as_posix()


def default_single_task_resume_state_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("resume_state.json").as_posix()


def default_scheduler_safe_lane_policy_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("scheduler_safe_lane_policy.json").as_posix()


def default_operator_proof_bundle_path(*, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path) if ledger_path is not None else Path(DEFAULT_SINGLE_TASK_LEDGER_PATH)
    return path.with_name("operator_proof_bundle.json").as_posix()


def build_single_task_run_token(
    *,
    task_path: str,
    task_text: str,
    provider: str | None,
    model: str | None,
    max_iters: int,
    push: bool,
    keep_runtime_artifacts: bool,
) -> str:
    payload = "|".join(
        [
            str(task_path or ""),
            hashlib.sha1(str(task_text or "").encode("utf-8", errors="replace")).hexdigest(),
            str(provider or ""),
            str(model or ""),
            str(int(max_iters)),
            "1" if push else "0",
            "1" if keep_runtime_artifacts else "0",
        ]
    )
    return hashlib.sha1(payload.encode("utf-8", errors="replace")).hexdigest()[:16]


def read_single_task_resume_state(*, resume_state_path: str | Path | None = None, ledger_path: str | Path | None = None) -> dict[str, object]:
    path = Path(resume_state_path or default_single_task_resume_state_path(ledger_path=ledger_path))
    if not path.exists():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    return dict(payload) if isinstance(payload, dict) else {}


def write_single_task_resume_state(
    state: Mapping[str, object],
    *,
    resume_state_path: str | Path | None = None,
    ledger_path: str | Path | None = None,
) -> str:
    target = Path(resume_state_path or state.get("resume_state_path") or default_single_task_resume_state_path(ledger_path=ledger_path))
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = dict(state)
    payload["resume_state_path"] = target.as_posix()
    target.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target.as_posix()


def _find_single_task_entry_by_run_token(entries: Sequence[Mapping[str, object]], run_token: str) -> dict[str, object]:
    for row in reversed([dict(entry) for entry in entries]):
        resume = dict(row.get("resume", {}) or {})
        if str(resume.get("run_token", "") or "") == str(run_token or ""):
            return row
    return {}


def _tail_text(text: str, *, limit: int = 1200) -> str:
    value = str(text or "")
    if len(value) <= limit:
        return value
    return value[-limit:]



def _safe_ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(float(numerator) / float(denominator), 4)



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





def build_single_task_multi_agent_role_artifacts(
    *,
    task_path: str,
    required_paths: Sequence[str],
    execution_summary: Mapping[str, object] | None,
    execution_invoked: bool,
    max_repair_attempts_within_run: int = 1,
) -> dict[str, object]:
    from agents.lib.controller import decide_single_task_controller_action  # type: ignore
    from agents.lib.failure_classifier import classify_single_task_failure  # type: ignore
    from agents.lib.failure_journal import build_multi_agent_failure_context  # type: ignore
    from agents.lib.repair_loop import select_single_task_targeted_repair  # type: ignore
    from agents.lib.repair_planner import build_single_task_repair_plan  # type: ignore
    from agents.lib.verifier import build_single_task_developer_artifact, build_single_task_verifier_artifact  # type: ignore

    developer_artifact = build_single_task_developer_artifact(
        task_path=task_path,
        required_paths=required_paths,
        command=list(dict(execution_summary or {}).get("command", []) or []),
        execution_summary=execution_summary,
        execution_invoked=execution_invoked,
    )
    verifier_artifact = build_single_task_verifier_artifact(
        task_path=task_path,
        developer_artifact=developer_artifact,
        execution_summary=execution_summary,
        execution_invoked=execution_invoked,
    )
    baseline_repair_artifact = select_single_task_targeted_repair(
        task_path=task_path,
        developer_artifact=developer_artifact,
        verifier_artifact=verifier_artifact,
        max_repair_attempts_within_run=max_repair_attempts_within_run,
    )
    failure_taxonomy = classify_single_task_failure(
        task_path=task_path,
        required_paths=required_paths,
        execution_summary=execution_summary,
        developer_artifact=developer_artifact,
        verifier_artifact=verifier_artifact,
    )
    repair_artifact = build_single_task_repair_plan(
        task_path=task_path,
        verifier_artifact=verifier_artifact,
        baseline_repair_artifact=baseline_repair_artifact,
        failure_taxonomy=failure_taxonomy,
    )
    controller_decision = decide_single_task_controller_action(
        task_path=task_path,
        developer_artifact=developer_artifact,
        verifier_artifact=verifier_artifact,
        repair_artifact=repair_artifact,
    )
    role_trace = [
        "developer_generation",
        "verifier_focused_validation",
        "verifier_full_validation",
        "repair_selection",
        "controller_decision",
    ]
    failure_context = build_multi_agent_failure_context(
        task_path=task_path,
        role_trace=role_trace,
        builder_artifact=developer_artifact,
        verifier_artifact=verifier_artifact,
        controller_decision=controller_decision,
    )
    return {
        "developer_artifact": developer_artifact,
        "verifier_artifact": verifier_artifact,
        "failure_taxonomy": failure_taxonomy,
        "repair_artifact": repair_artifact,
        "controller_decision": controller_decision,
        "role_trace": role_trace,
        "failure_context": failure_context,
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
    run_token: str = "",
    resume_state_path: str = "",
    resume_reentry: bool = False,
    reused_completed_entry: bool = False,
    resume_count: int = 0,
    resumed_from_stage: str = "",
    multi_agent_loop: Mapping[str, object] | None = None,
) -> dict[str, object]:
    admission_dict = dict(admission)
    proof_dict = dict(proof_admission)
    execution = dict(execution_summary or {})
    multi_agent_payload = dict(multi_agent_loop or {})
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
        "resume": {
            "run_token": str(run_token or ""),
            "resume_state_path": str(resume_state_path or ""),
            "resume_reentry": bool(resume_reentry),
            "reused_completed_entry": bool(reused_completed_entry),
            "resume_count": int(resume_count or 0),
            "resumed_from_stage": str(resumed_from_stage or ""),
        },
        "final_decision": final_decision,
        "execution": {
            "command": list(execution.get("command", []) or []),
            "stdout_tail": str(execution.get("stdout_tail", "") or ""),
            "stderr_tail": str(execution.get("stderr_tail", "") or ""),
        },
        "task_excerpt": _tail_text(task_text, limit=400),
        "multi_agent_loop": {
            "role_trace": list(multi_agent_payload.get("role_trace", []) or []),
            "developer_artifact": dict(multi_agent_payload.get("developer_artifact", {}) or {}),
            "verifier_artifact": dict(multi_agent_payload.get("verifier_artifact", {}) or {}),
            "failure_taxonomy": dict(multi_agent_payload.get("failure_taxonomy", {}) or {}),
            "repair_artifact": dict(multi_agent_payload.get("repair_artifact", {}) or {}),
            "controller_decision": dict(multi_agent_payload.get("controller_decision", {}) or {}),
            "failure_context": dict(multi_agent_payload.get("failure_context", {}) or {}),
        },
    }



def append_single_task_run_ledger_entry(entry: Mapping[str, object], *, ledger_path: str | Path | None = None) -> str:
    path = Path(ledger_path or entry.get("ledger_path") or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(dict(entry), sort_keys=True) + "\n")
    return path.as_posix()



def read_single_task_run_ledger(*, ledger_path: str | Path | None = None) -> list[dict[str, object]]:
    path = Path(ledger_path or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    if not path.exists():
        return []
    rows: list[dict[str, object]] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line:
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(dict(payload))
    return rows



def build_single_task_canary_metrics(
    *,
    entries: Sequence[Mapping[str, object]] | None = None,
    ledger_path: str | Path | None = None,
    generated_at: str = "",
) -> dict[str, object]:
    rows = [dict(entry) for entry in (entries or read_single_task_run_ledger(ledger_path=ledger_path))]
    source_ledger_path = str(ledger_path or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    total_runs = len(rows)

    stop_reason_counts = {
        "completed": 0,
        "blocked_supervised_only": 0,
        "escalation_required": 0,
        "execution_failed": 0,
    }
    lane_counts = {
        "autonomous_safe": 0,
        "supervised_only": 0,
        "escalation_required": 0,
    }
    allowlist_family_counts: dict[str, int] = {}
    admitted_runs = 0
    executed_runs = 0
    completed_runs = 0
    execution_failed_runs = 0
    blocked_runs = 0
    hosted_authority_blocked_runs = 0
    runs_with_retry_observed = 0
    completed_after_retry_runs = 0
    total_retry_count_observed = 0
    max_retry_count_observed = 0
    missing_deliverable_retry_runs = 0
    coupled_compatibility_repair_runs = 0
    last_green_subset_preserved_runs = 0

    for row in rows:
        admission = dict(row.get("admission", {}) or {})
        retry = dict(row.get("retry", {}) or {})
        validation = dict(row.get("validation", {}) or {})
        final_decision = str(row.get("final_decision", "") or "")
        lane = str(admission.get("autonomous_single_task_lane", "") or "")
        allowlist_family = str(admission.get("autonomy_allowlist_family", "") or "")

        if final_decision in stop_reason_counts:
            stop_reason_counts[final_decision] += 1
        if lane in lane_counts:
            lane_counts[lane] += 1
        if allowlist_family:
            allowlist_family_counts[allowlist_family] = allowlist_family_counts.get(allowlist_family, 0) + 1

        proof_allowed = bool(admission.get("proof_task_admission_allowed", False))
        autonomous_allowed = bool(admission.get("autonomous_single_task_allowed", False))
        if autonomous_allowed and proof_allowed:
            admitted_runs += 1
        if bool(validation.get("execution_invoked", False)):
            executed_runs += 1
        if final_decision == "completed":
            completed_runs += 1
        elif final_decision == "execution_failed":
            execution_failed_runs += 1
            blocked_runs += 1
        elif final_decision in {"blocked_supervised_only", "escalation_required"}:
            blocked_runs += 1

        if bool(validation.get("no_checks_reported_observed", False)):
            hosted_authority_blocked_runs += 1

        retry_count = int(retry.get("retry_count_observed", 0) or 0)
        total_retry_count_observed += retry_count
        max_retry_count_observed = max(max_retry_count_observed, retry_count)
        if retry_count > 0:
            runs_with_retry_observed += 1
            if final_decision == "completed":
                completed_after_retry_runs += 1
        if bool(retry.get("missing_deliverable_retry_observed", False)):
            missing_deliverable_retry_runs += 1
        if bool(retry.get("coupled_compatibility_repair_observed", False)):
            coupled_compatibility_repair_runs += 1
        if bool(retry.get("last_green_subset_preserved_observed", False)):
            last_green_subset_preserved_runs += 1

    return {
        "schema_version": CANARY_METRICS_SCHEMA_VERSION,
        "report_type": "autonomous_single_task_canary_metrics",
        "generated_at": str(generated_at or ""),
        "ledger_path": source_ledger_path,
        "total_runs": total_runs,
        "admitted_runs": admitted_runs,
        "executed_runs": executed_runs,
        "completed_runs": completed_runs,
        "blocked_runs": blocked_runs,
        "execution_failed_runs": execution_failed_runs,
        "completion_rate": _safe_ratio(completed_runs, admitted_runs),
        "hosted_authority_blocked_runs": hosted_authority_blocked_runs,
        "hosted_authority_blocking_frequency": _safe_ratio(hosted_authority_blocked_runs, total_runs),
        "retry_metrics": {
            "runs_with_retry_observed": runs_with_retry_observed,
            "completed_after_retry_runs": completed_after_retry_runs,
            "retry_convergence_rate": _safe_ratio(completed_after_retry_runs, runs_with_retry_observed),
            "average_retry_count_per_admitted_run": _safe_ratio(total_retry_count_observed, admitted_runs),
            "max_retry_count_observed": max_retry_count_observed,
            "missing_deliverable_retry_runs": missing_deliverable_retry_runs,
            "coupled_compatibility_repair_runs": coupled_compatibility_repair_runs,
            "last_green_subset_preserved_runs": last_green_subset_preserved_runs,
        },
        "stop_reason_counts": stop_reason_counts,
        "lane_counts": lane_counts,
        "allowlist_family_counts": allowlist_family_counts,
    }



def write_single_task_canary_metrics(
    metrics: Mapping[str, object],
    *,
    metrics_path: str | Path | None = None,
) -> str:
    target = Path(metrics_path or default_single_task_canary_metrics_path(ledger_path=metrics.get("ledger_path")))
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(metrics), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target.as_posix()



def _dedupe_paths(paths: Sequence[str] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in paths or []:
        value = str(raw or "").strip()
        if not value or value in seen:
            continue
        ordered.append(value)
        seen.add(value)
    return ordered



def _single_task_handoff_kind(final_decision: str) -> str:
    if final_decision == "escalation_required":
        return "escalation_required"
    if final_decision == "blocked_supervised_only":
        return "supervised_only"
    if final_decision == "execution_failed":
        return "supervised_recovery"
    return "none"



def _single_task_handoff_implicated_paths(entry: Mapping[str, object] | None) -> list[str]:
    payload = dict(entry or {})
    admission = dict(payload.get("admission", {}) or {})
    control_plane_paths = _dedupe_paths(admission.get("self_hosting_control_plane_required_paths", []) or [])
    if control_plane_paths:
        return control_plane_paths
    return _dedupe_paths(payload.get("required_paths", []) or [])



def _single_task_handoff_reason(entry: Mapping[str, object] | None) -> str:
    payload = dict(entry or {})
    escalation = dict(payload.get("escalation", {}) or {})
    admission = dict(payload.get("admission", {}) or {})
    final_decision = str(payload.get("final_decision", "") or "")
    reason = str(escalation.get("reason", "") or "").strip()
    if reason:
        return reason
    if final_decision == "blocked_supervised_only":
        return str(
            admission.get("proof_task_admission_reason")
            or admission.get("autonomous_single_task_rationale")
            or "Task was not admitted to the bounded safe autonomous single-task lane."
        )
    if final_decision == "execution_failed":
        return "Admitted single-task run failed and should be handed back to supervised recovery."
    return ""



def _single_task_next_supervised_action(entry: Mapping[str, object] | None) -> str:
    payload = dict(entry or {})
    final_decision = str(payload.get("final_decision", "") or "")
    admission = dict(payload.get("admission", {}) or {})
    if final_decision == "escalation_required":
        if bool(admission.get("self_hosting_control_plane_task", False)):
            return (
                "Run this task in a supervised/manual lane and keep self-hosting control-plane edits escalation-first; "
                "review the implicated harness files before attempting any targeted change."
            )
        return (
            "Run this task in a supervised/manual lane because it remains outside the bounded safe autonomous slice."
        )
    if final_decision == "blocked_supervised_only":
        return (
            "Run this task through the supervised run_task lane, then revisit task decomposition or allowlist policy only "
            "after the bounded task shape is clearer."
        )
    if final_decision == "execution_failed":
        return (
            "Inspect the console output, _last_agent_model_output.txt, and _last_agent_file_bundle.txt, then apply the "
            "smallest targeted supervised recovery on the implicated files."
        )
    return ""



def build_single_task_supervised_handoff_artifact(
    *,
    entry: Mapping[str, object] | None,
    handoff_path: str | Path | None = None,
    generated_at: str = "",
) -> dict[str, object]:
    payload = dict(entry or {})
    admission = dict(payload.get("admission", {}) or {})
    validation = dict(payload.get("validation", {}) or {})
    final_decision = str(payload.get("final_decision", "") or "")
    artifact_path = str(handoff_path or default_single_task_supervised_handoff_path(ledger_path=payload.get("ledger_path")))
    implicated_paths = _single_task_handoff_implicated_paths(payload)
    handoff_required = final_decision != "completed"
    suggested_inputs = []
    if final_decision == "execution_failed":
        suggested_inputs = [
            "console output",
            "_last_agent_model_output.txt",
            "_last_agent_file_bundle.txt",
        ]

    return {
        "schema_version": SUPERVISED_HANDOFF_SCHEMA_VERSION,
        "artifact_type": "autonomous_single_task_supervised_handoff",
        "generated_at": str(generated_at or payload.get("completed_at") or payload.get("started_at") or ""),
        "handoff_path": artifact_path,
        "task_path": str(payload.get("task_path", "") or ""),
        "task_name": str(payload.get("task_name", "") or Path(str(payload.get("task_path", "") or "")).name),
        "final_decision": final_decision,
        "handoff_required": handoff_required,
        "handoff_kind": _single_task_handoff_kind(final_decision),
        "handoff_reason": _single_task_handoff_reason(payload),
        "next_supervised_action": _single_task_next_supervised_action(payload),
        "implicated_paths": implicated_paths,
        "suggested_inputs": suggested_inputs,
        "admission_surface": {
            "autonomous_single_task_lane": str(admission.get("autonomous_single_task_lane", "") or ""),
            "autonomy_allowlist_family": str(admission.get("autonomy_allowlist_family", "") or ""),
            "self_hosting_control_plane_task": bool(admission.get("self_hosting_control_plane_task", False)),
            "proof_task_detected": bool(admission.get("proof_task_detected", False)),
            "proof_task_admission_allowed": bool(admission.get("proof_task_admission_allowed", False)),
        },
        "validation_surface": {
            "execution_invoked": bool(validation.get("execution_invoked", False)),
            "returncode": validation.get("returncode"),
            "no_checks_reported_observed": bool(validation.get("no_checks_reported_observed", False)),
        },
    }



def write_single_task_supervised_handoff_artifact(
    artifact: Mapping[str, object],
    *,
    handoff_path: str | Path | None = None,
) -> str:
    target = Path(handoff_path or artifact.get("handoff_path") or DEFAULT_SINGLE_TASK_SUPERVISED_HANDOFF_PATH)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(artifact), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target.as_posix()



def refresh_single_task_reporting_artifacts(
    *,
    ledger_path: str | Path | None = None,
    metrics_path: str | Path | None = None,
    recovery_report_path: str | Path | None = None,
    supervised_handoff_path: str | Path | None = None,
    current_entry: Mapping[str, object] | None = None,
    generated_at: str = "",
) -> dict[str, object]:
    from agents.lib.failure_journal import (  # type: ignore
        build_autonomous_single_task_recovery_report,
        write_autonomous_single_task_recovery_report,
    )

    source_ledger_path = str(ledger_path or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    entries = read_single_task_run_ledger(ledger_path=source_ledger_path)
    metrics = build_single_task_canary_metrics(
        entries=entries,
        ledger_path=source_ledger_path,
        generated_at=generated_at,
    )
    metrics_artifact_path = write_single_task_canary_metrics(metrics, metrics_path=metrics_path)
    recovery_report = build_autonomous_single_task_recovery_report(
        entries=entries,
        ledger_path=source_ledger_path,
        generated_at=generated_at,
    )
    recovery_artifact_path = write_autonomous_single_task_recovery_report(
        recovery_report,
        report_path=recovery_report_path or default_single_task_recovery_report_path(ledger_path=source_ledger_path),
    )
    active_entry = dict(current_entry or (entries[-1] if entries else {}))
    supervised_handoff = build_single_task_supervised_handoff_artifact(
        entry=active_entry,
        handoff_path=supervised_handoff_path or default_single_task_supervised_handoff_path(ledger_path=source_ledger_path),
        generated_at=generated_at,
    )
    supervised_handoff_artifact_path = write_single_task_supervised_handoff_artifact(
        supervised_handoff,
        handoff_path=supervised_handoff_path or default_single_task_supervised_handoff_path(ledger_path=source_ledger_path),
    )
    return {
        "ledger_entries": entries,
        "canary_metrics": metrics,
        "canary_metrics_path": metrics_artifact_path,
        "recovery_report": recovery_report,
        "recovery_report_path": recovery_artifact_path,
        "supervised_handoff": supervised_handoff,
        "supervised_handoff_path": supervised_handoff_artifact_path,
    }





def write_scheduler_safe_lane_policy_artifact(
    artifact: Mapping[str, object],
    *,
    policy_artifact_path: str | Path | None = None,
) -> str:
    target = Path(policy_artifact_path or artifact.get("policy_artifact_path") or default_scheduler_safe_lane_policy_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(artifact), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target.as_posix()


def run_scheduler_single_task_bridge(
    *,
    queue: Sequence[object],
    repo_root: str | Path = ".",
    completed_task_paths: Sequence[str] | None = None,
    selection: Mapping[str, object] | None = None,
    selector: Callable[..., Mapping[str, object]] | None = None,
    single_task_runner: Callable[..., Mapping[str, object]] | None = None,
    runner_kwargs: Mapping[str, object] | None = None,
) -> dict[str, object]:
    active_selection = dict(selection or {})
    if not active_selection:
        if selector is not None:
            active_selection = dict(
                selector(
                    queue,
                    repo_root=repo_root,
                    completed_task_paths=completed_task_paths,
                )
            )
        else:
            try:
                from agents.lib.task_queue import select_single_admissible_safe_task as _select_single_admissible_safe_task  # type: ignore

                active_selection = dict(
                    _select_single_admissible_safe_task(
                        queue,
                        repo_root=repo_root,
                        completed_task_paths=completed_task_paths,
                    )
                )
            except ImportError:
                from agents.lib.task_queue import plan_safe_lane_stop_requeue_policy as _plan_safe_lane_stop_requeue_policy

                planned = dict(
                    _plan_safe_lane_stop_requeue_policy(
                        queue,
                        completed_task_paths=completed_task_paths,
                    )
                )
                active_selection = dict(planned)
                active_selection.setdefault(
                    "bridge_decision",
                    "delegate_to_single_task_runner" if str(planned.get("selected_task_path", "") or "") else "delegate_to_supervision",
                )
    decision = str(active_selection.get("bridge_decision", "") or "")
    selected_task_path = str(active_selection.get("selected_task_path", "") or "")
    if not decision:
        decision = "delegate_to_single_task_runner" if selected_task_path else "delegate_to_supervision"
    if decision != "delegate_to_single_task_runner" or not selected_task_path:
        return {
            "bridge_decision": decision or "delegate_to_supervision",
            "autonomous_single_task_invoked": False,
            "task_path": selected_task_path,
            "selection": active_selection,
            "rationale": str(active_selection.get("rationale", "") or ""),
        }

    result = dict(
        (single_task_runner or run_autonomous_single_task)(
            selected_task_path,
            **dict(runner_kwargs or {}),
        )
    )
    entry = dict(result.get("entry", {}) or {})
    return {
        "bridge_decision": "delegate_to_single_task_runner",
        "autonomous_single_task_invoked": True,
        "task_path": selected_task_path,
        "selection": active_selection,
        "single_task_result": result,
        "final_decision": str(entry.get("final_decision", "") or ""),
    }


def run_scheduler_safe_lane_bridge(
    queue: Sequence[object],
    *,
    completed_task_paths: Sequence[str] | None = None,
    task_text_loader: Callable[[str], str] | None = None,
    task_runner: Callable[..., Mapping[str, object]] | None = None,
    policy_artifact_path: str | Path | None = None,
    now: Callable[[], str] | None = None,
    **runner_kwargs: object,
) -> dict[str, object]:
    from agents.lib.task_queue import plan_safe_lane_stop_requeue_policy

    selection = dict(
        plan_safe_lane_stop_requeue_policy(
            queue,
            completed_task_paths=completed_task_paths,
            task_text_loader=task_text_loader,
        )
    )
    autonomous_result: dict[str, object] | None = None
    selected_task_path = str(selection.get("selected_task_path", "") or "")
    if selected_task_path:
        autonomous_result = dict((task_runner or run_autonomous_single_task)(selected_task_path, **runner_kwargs))
    generated_at = str((now or (lambda: ""))() or "")
    entry = dict(dict(autonomous_result or {}).get("entry", {}) or {})
    artifact = {
        "artifact_type": "scheduler_safe_lane_mix_policy",
        "generated_at": generated_at,
        "policy_artifact_path": str(policy_artifact_path or default_scheduler_safe_lane_policy_path()),
        "policy_decision": str(selection.get("decision", "") or ""),
        "selected_task_path": selected_task_path,
        "executed_autonomous_task": bool(selected_task_path and autonomous_result),
        "autonomous_task_final_decision": str(entry.get("final_decision", "") or ""),
        "ready_safe_task_paths": list(selection.get("ready_safe_task_paths", []) or []),
        "supervised_handoff_task_paths": list(selection.get("supervised_handoff_task_paths", []) or []),
        "supervised_handoff_required": bool(selection.get("supervised_handoff_required", False)),
        "requeue_task_paths": list(selection.get("requeue_task_paths", []) or []),
        "waiting_task_paths": list(selection.get("waiting_task_paths", []) or []),
        "stop_after_selected": bool(selection.get("stop_after_selected", False)),
        "rationale": str(selection.get("rationale", "") or ""),
    }
    written = write_scheduler_safe_lane_policy_artifact(artifact, policy_artifact_path=policy_artifact_path or default_scheduler_safe_lane_policy_path())
    return {
        "selection": selection,
        "autonomous_result": autonomous_result,
        "policy_artifact": artifact,
        "policy_artifact_path": written,
    }


def _real_pr_smoke_status(smoke: Mapping[str, object] | None = None) -> str:
    payload = dict(smoke or {})
    for key in ("required_check_contract_status", "smoke_proof_status", "probe_status", "status"):
        value = str(payload.get(key, "") or "")
        if value:
            return value
    return ""


def _real_pr_smoke_satisfied(smoke: Mapping[str, object] | None = None) -> bool:
    payload = dict(smoke or {})
    if bool(payload.get("required_check_contract_satisfied", False)) or bool(payload.get("contract_satisfied", False)):
        return True
    return _real_pr_smoke_status(payload) == "satisfied"


def build_live_canary_operator_proof_bundle(
    *,
    real_pr_smoke: Mapping[str, object] | None = None,
    safe_result: Mapping[str, object] | None = None,
    escalation_result: Mapping[str, object] | None = None,
    proof_bundle_path: str | Path | None = None,
    generated_at: str = "",
) -> dict[str, object]:
    smoke = dict(real_pr_smoke or {})
    safe_payload = dict(safe_result or {})
    escalation_payload = dict(escalation_result or {})
    safe_entry = dict(safe_payload.get("entry", {}) or {})
    escalation_entry = dict(escalation_payload.get("entry", {}) or {})
    canary_metrics = dict(escalation_payload.get("canary_metrics", {}) or safe_payload.get("canary_metrics", {}) or {})
    recovery_report = dict(escalation_payload.get("recovery_report", {}) or safe_payload.get("recovery_report", {}) or {})
    supervised_handoff = dict(escalation_payload.get("supervised_handoff", {}) or safe_payload.get("supervised_handoff", {}) or {})
    smoke_status = _real_pr_smoke_status(smoke)
    smoke_satisfied = _real_pr_smoke_satisfied(smoke)
    safe_completed = str(safe_entry.get("final_decision", "") or "") == "completed" and bool(dict(safe_entry.get("validation", {}) or {}).get("execution_invoked", False))
    escalation_explicit = str(escalation_entry.get("final_decision", "") or "") in {"escalation_required", "blocked_supervised_only"} and bool(supervised_handoff.get("handoff_required", dict(escalation_entry.get("escalation", {}) or {}).get("required", False)))
    claim_blockers: list[str] = []
    if not smoke_satisfied:
        claim_blockers.append("real_github_required_check_not_yet_satisfied")
    if not safe_completed:
        claim_blockers.append("safe_canary_case_not_completed")
    if not escalation_explicit:
        claim_blockers.append("explicit_out_of_lane_escalation_case_missing")
    bounded_claim_ready = not claim_blockers
    ledger_path = str(escalation_payload.get("ledger_path") or safe_payload.get("ledger_path") or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    bundle_path = str(proof_bundle_path or default_operator_proof_bundle_path(ledger_path=ledger_path))
    return {
        "schema_version": OPERATOR_PROOF_BUNDLE_SCHEMA_VERSION,
        "bundle_type": "bounded_single_task_operator_proof_bundle",
        "generated_at": str(generated_at or ""),
        "proof_bundle_path": bundle_path,
        "bounded_claim": "The orchestrator can run one allowlisted safe task at a time under supervised real-GitHub conditions.",
        "bounded_claim_ready": bounded_claim_ready,
        "claim_blockers": claim_blockers,
        "refused_claims": [
            "broad unattended scheduler autonomy",
            "multi-task autonomous execution",
            "arbitrary self-hosting control-plane autonomy",
        ],
        "hosted_authority": {
            "required_check_context": str(smoke.get("required_check_context", "ci-required") or "ci-required"),
            "status": smoke_status,
            "satisfied": smoke_satisfied,
            "pull_request_url": str(smoke.get("pull_request_url", "") or ""),
            "pull_request_number": int(smoke.get("pull_request_number", 0) or 0),
            "head_sha": str(smoke.get("head_sha", "") or ""),
            "note": str(smoke.get("note") or smoke.get("status_note") or ""),
        },
        "live_canary_corpus": {
            "safe_case": {
                "task_path": str(safe_payload.get("task_path", safe_entry.get("task_path", "")) or ""),
                "lane": str(dict(safe_entry.get("admission", {}) or {}).get("autonomous_single_task_lane", "") or ""),
                "final_decision": str(safe_entry.get("final_decision", "") or ""),
                "execution_invoked": bool(dict(safe_entry.get("validation", {}) or {}).get("execution_invoked", False)),
            },
            "explicit_escalation_case": {
                "task_path": str(escalation_payload.get("task_path", escalation_entry.get("task_path", "")) or ""),
                "lane": str(dict(escalation_entry.get("admission", {}) or {}).get("autonomous_single_task_lane", "") or ""),
                "final_decision": str(escalation_entry.get("final_decision", "") or ""),
                "handoff_required": bool(supervised_handoff.get("handoff_required", False)),
                "handoff_kind": str(supervised_handoff.get("handoff_kind", "") or ""),
                "implicated_paths": list(supervised_handoff.get("implicated_paths", []) or []),
            },
            "bounded_to_one_task_at_a_time": int(canary_metrics.get("total_runs", 0) or 0) <= 2,
        },
        "durable_artifacts": {
            "ledger_path": ledger_path,
            "canary_metrics_path": str(escalation_payload.get("canary_metrics_path", safe_payload.get("canary_metrics_path", "")) or ""),
            "recovery_report_path": str(escalation_payload.get("recovery_report_path", safe_payload.get("recovery_report_path", "")) or ""),
            "supervised_handoff_path": str(escalation_payload.get("supervised_handoff_path", safe_payload.get("supervised_handoff_path", "")) or ""),
            "resume_state_path": str(escalation_payload.get("resume_state_path", safe_payload.get("resume_state_path", "")) or ""),
        },
        "reporting_summary": {
            "total_runs": int(canary_metrics.get("total_runs", 0) or 0),
            "completed_runs": int(canary_metrics.get("completed_runs", 0) or 0),
            "handoff_required_count": int(recovery_report.get("handoff_required_count", 0) or 0),
            "escalation_required_count": int(recovery_report.get("escalation_required_count", 0) or 0),
            "hosted_authority_blocked_runs": int(recovery_report.get("hosted_authority_blocked_runs", 0) or 0),
        },
        "operator_next_action": (
            "Use the bounded one-task lane only for allowlisted ordinary work and keep out-of-lane work in the supervised/manual lane."
            if bounded_claim_ready
            else "Do not widen autonomy claims; inspect claim_blockers and continue under supervised/manual handling."
        ),
    }


def write_live_canary_operator_proof_bundle(bundle: Mapping[str, object], *, proof_bundle_path: str | Path | None = None) -> str:
    target = Path(proof_bundle_path or bundle.get("proof_bundle_path") or default_operator_proof_bundle_path())
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(dict(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return target.as_posix()


def run_live_canary_corpus_and_operator_proof_bundle(
    *,
    safe_task_path: str,
    escalation_task_path: str,
    real_pr_smoke_result: Mapping[str, object] | None = None,
    real_pr_smoke_runner: Callable[[], Mapping[str, object]] | None = None,
    provider: str | None = None,
    model: str | None = None,
    max_iters: int = 4,
    push: bool = False,
    keep_runtime_artifacts: bool = False,
    ledger_path: str | Path | None = None,
    metrics_path: str | Path | None = None,
    recovery_report_path: str | Path | None = None,
    supervised_handoff_path: str | Path | None = None,
    resume_state_path: str | Path | None = None,
    proof_bundle_path: str | Path | None = None,
    now: Callable[[], str] | None = None,
    executor: Callable[[Sequence[str]], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    smoke = dict(real_pr_smoke_result or ((real_pr_smoke_runner or (lambda: {}))() or {}))
    safe_result = run_autonomous_single_task(
        safe_task_path,
        provider=provider,
        model=model,
        max_iters=max_iters,
        push=push,
        keep_runtime_artifacts=keep_runtime_artifacts,
        ledger_path=ledger_path,
        metrics_path=metrics_path,
        recovery_report_path=recovery_report_path,
        supervised_handoff_path=supervised_handoff_path,
        resume_state_path=resume_state_path,
        now=now,
        executor=executor,
    )
    escalation_result = run_autonomous_single_task(
        escalation_task_path,
        provider=provider,
        model=model,
        max_iters=max_iters,
        push=push,
        keep_runtime_artifacts=keep_runtime_artifacts,
        ledger_path=ledger_path or safe_result.get("ledger_path"),
        metrics_path=metrics_path or safe_result.get("canary_metrics_path"),
        recovery_report_path=recovery_report_path or safe_result.get("recovery_report_path"),
        supervised_handoff_path=supervised_handoff_path or safe_result.get("supervised_handoff_path"),
        resume_state_path=resume_state_path or safe_result.get("resume_state_path"),
        now=now,
        executor=executor,
    )
    generated_at = str((now or (lambda: ""))() or dict(escalation_result.get("entry", {}) or {}).get("completed_at", ""))
    bundle = build_live_canary_operator_proof_bundle(
        real_pr_smoke=smoke,
        safe_result=safe_result,
        escalation_result=escalation_result,
        proof_bundle_path=proof_bundle_path or default_operator_proof_bundle_path(ledger_path=escalation_result.get("ledger_path")),
        generated_at=generated_at,
    )
    written = write_live_canary_operator_proof_bundle(bundle, proof_bundle_path=proof_bundle_path or bundle.get("proof_bundle_path"))
    return {
        "real_pr_smoke": smoke,
        "safe_result": safe_result,
        "escalation_result": escalation_result,
        "proof_bundle": bundle,
        "proof_bundle_path": written,
    }


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
    metrics_path: str | Path | None = None,
    recovery_report_path: str | Path | None = None,
    supervised_handoff_path: str | Path | None = None,
    resume_state_path: str | Path | None = None,
    now: Callable[[], str] | None = None,
    executor: Callable[[Sequence[str]], Mapping[str, object]] | None = None,
) -> dict[str, object]:
    import agents.run_task as run_task

    ledger_location = str(ledger_path or DEFAULT_SINGLE_TASK_LEDGER_PATH)
    resume_location = str(resume_state_path or default_single_task_resume_state_path(ledger_path=ledger_location))
    task_file = Path(task_path)
    if not task_file.exists():
        raise FileNotFoundError(f"Task file not found: {task_path}")
    task_text = task_file.read_text(encoding="utf-8", errors="replace")
    required_paths = list(run_task.parse_required_files(task_text))
    run_token = build_single_task_run_token(
        task_path=task_file.as_posix(),
        task_text=task_text,
        provider=provider,
        model=model,
        max_iters=max_iters,
        push=push,
        keep_runtime_artifacts=keep_runtime_artifacts,
    )

    existing_entries = read_single_task_run_ledger(ledger_path=ledger_location)
    existing_entry = _find_single_task_entry_by_run_token(existing_entries, run_token)
    clock = now or (lambda: "")

    if existing_entry:
        existing_resume = dict(existing_entry.get("resume", {}) or {})
        if not existing_resume.get("resume_state_path"):
            existing_resume["resume_state_path"] = resume_location
            existing_entry["resume"] = existing_resume
        write_single_task_resume_state(
            {
                "schema_version": 1,
                "runner": "autonomous_single_task",
                "run_token": run_token,
                "task_path": task_file.as_posix(),
                "ledger_path": ledger_location,
                "resume_state_path": resume_location,
                "stage": "completed",
                "resume_count": int(existing_resume.get("resume_count", 0) or 0),
                "reused_completed_entry": True,
                "latest_started_at": str(existing_entry.get("started_at", "") or ""),
                "latest_completed_at": str(existing_entry.get("completed_at", "") or ""),
            },
            resume_state_path=resume_location,
            ledger_path=ledger_location,
        )
        refreshed = refresh_single_task_reporting_artifacts(
            ledger_path=ledger_location,
            metrics_path=metrics_path,
            recovery_report_path=recovery_report_path,
            supervised_handoff_path=supervised_handoff_path,
            current_entry=existing_entry,
            generated_at=str(existing_entry.get("completed_at", "") or existing_entry.get("started_at", "") or ""),
        )
        existing_multi_agent_loop = dict(existing_entry.get("multi_agent_loop", {}) or {})
        return {
            "task_path": task_file.as_posix(),
            "ledger_path": ledger_location,
            "entry": existing_entry,
            "resume_state_path": resume_location,
            "reused_completed_entry": True,
            "canary_metrics_path": refreshed["canary_metrics_path"],
            "canary_metrics": refreshed["canary_metrics"],
            "recovery_report_path": refreshed["recovery_report_path"],
            "recovery_report": refreshed["recovery_report"],
            "supervised_handoff_path": refreshed["supervised_handoff_path"],
            "supervised_handoff": refreshed["supervised_handoff"],
            "multi_agent_loop": existing_multi_agent_loop,
            "role_trace": list(existing_multi_agent_loop.get("role_trace", []) or []),
            "developer_artifact": dict(existing_multi_agent_loop.get("developer_artifact", {}) or {}),
            "verifier_artifact": dict(existing_multi_agent_loop.get("verifier_artifact", {}) or {}),
            "failure_taxonomy": dict(existing_multi_agent_loop.get("failure_taxonomy", {}) or {}),
            "repair_artifact": dict(existing_multi_agent_loop.get("repair_artifact", {}) or {}),
            "controller_decision": dict(existing_multi_agent_loop.get("controller_decision", {}) or {}),
        }

    prior_resume_state = read_single_task_resume_state(resume_state_path=resume_location, ledger_path=ledger_location)
    resumed_from_stage = ""
    resume_count = 0
    resume_reentry = False
    if str(prior_resume_state.get("run_token", "") or "") == run_token and str(prior_resume_state.get("stage", "") or "") != "completed":
        resume_reentry = True
        resumed_from_stage = str(prior_resume_state.get("stage", "") or "")
        resume_count = int(prior_resume_state.get("resume_count", 0) or 0) + 1

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

    started_at = str(clock() or "")
    write_single_task_resume_state(
        {
            "schema_version": 1,
            "runner": "autonomous_single_task",
            "run_token": run_token,
            "task_path": task_file.as_posix(),
            "ledger_path": ledger_location,
            "resume_state_path": resume_location,
            "stage": "admitted",
            "resume_count": resume_count,
            "resume_reentry": resume_reentry,
            "resumed_from_stage": resumed_from_stage,
            "latest_started_at": started_at,
            "admission_allowed": bool(admission.get("autonomous_single_task_allowed", False)),
            "proof_admission_allowed": bool(proof_admission.get("proof_task_admission_allowed", False)),
        },
        resume_state_path=resume_location,
        ledger_path=ledger_location,
    )

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
        write_single_task_resume_state(
            {
                "schema_version": 1,
                "runner": "autonomous_single_task",
                "run_token": run_token,
                "task_path": task_file.as_posix(),
                "ledger_path": ledger_location,
                "resume_state_path": resume_location,
                "stage": "executing",
                "resume_count": resume_count,
                "resume_reentry": resume_reentry,
                "resumed_from_stage": resumed_from_stage,
                "latest_started_at": started_at,
                "command": command,
            },
            resume_state_path=resume_location,
            ledger_path=ledger_location,
        )
        raw_execution = dict((executor or _default_executor)(command))
        execution_summary = summarize_single_task_execution(execution_result=raw_execution)
    multi_agent_loop = build_single_task_multi_agent_role_artifacts(
        task_path=task_file.as_posix(),
        required_paths=required_paths,
        execution_summary=execution_summary,
        execution_invoked=allowed,
    )
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
        run_token=run_token,
        resume_state_path=resume_location,
        resume_reentry=resume_reentry,
        reused_completed_entry=False,
        resume_count=resume_count,
        resumed_from_stage=resumed_from_stage,
        multi_agent_loop=multi_agent_loop,
    )
    write_single_task_resume_state(
        {
            "schema_version": 1,
            "runner": "autonomous_single_task",
            "run_token": run_token,
            "task_path": task_file.as_posix(),
            "ledger_path": ledger_location,
            "resume_state_path": resume_location,
            "stage": "finalizing",
            "resume_count": resume_count,
            "resume_reentry": resume_reentry,
            "resumed_from_stage": resumed_from_stage,
            "latest_started_at": started_at,
            "latest_completed_at": completed_at,
        },
        resume_state_path=resume_location,
        ledger_path=ledger_location,
    )
    persisted_path = append_single_task_run_ledger_entry(entry, ledger_path=ledger_location)
    reporting = refresh_single_task_reporting_artifacts(
        ledger_path=ledger_location,
        metrics_path=metrics_path,
        recovery_report_path=recovery_report_path,
        supervised_handoff_path=supervised_handoff_path,
        current_entry=entry,
        generated_at=str(completed_at or started_at),
    )
    write_single_task_resume_state(
        {
            "schema_version": 1,
            "runner": "autonomous_single_task",
            "run_token": run_token,
            "task_path": task_file.as_posix(),
            "ledger_path": persisted_path,
            "resume_state_path": resume_location,
            "stage": "completed",
            "resume_count": resume_count,
            "resume_reentry": resume_reentry,
            "resumed_from_stage": resumed_from_stage,
            "latest_started_at": started_at,
            "latest_completed_at": completed_at,
            "final_decision": str(entry.get("final_decision", "") or ""),
        },
        resume_state_path=resume_location,
        ledger_path=ledger_location,
    )
    return {
        "task_path": task_file.as_posix(),
        "ledger_path": persisted_path,
        "entry": entry,
        "resume_state_path": resume_location,
        "reused_completed_entry": False,
        "canary_metrics_path": reporting["canary_metrics_path"],
        "canary_metrics": reporting["canary_metrics"],
        "recovery_report_path": reporting["recovery_report_path"],
        "recovery_report": reporting["recovery_report"],
        "supervised_handoff_path": reporting["supervised_handoff_path"],
        "supervised_handoff": reporting["supervised_handoff"],
        "multi_agent_loop": multi_agent_loop,
        "role_trace": list(multi_agent_loop.get("role_trace", []) or []),
        "developer_artifact": dict(multi_agent_loop.get("developer_artifact", {}) or {}),
        "verifier_artifact": dict(multi_agent_loop.get("verifier_artifact", {}) or {}),
        "failure_taxonomy": dict(multi_agent_loop.get("failure_taxonomy", {}) or {}),
        "repair_artifact": dict(multi_agent_loop.get("repair_artifact", {}) or {}),
        "controller_decision": dict(multi_agent_loop.get("controller_decision", {}) or {}),
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
    ap.add_argument("--metrics-path", default=None)
    ap.add_argument("--recovery-report-path", default=None)
    ap.add_argument("--supervised-handoff-path", default=None)
    ap.add_argument("--resume-state-path", default=None)
    args = ap.parse_args()

    result = run_autonomous_single_task(
        args.task,
        provider=args.provider,
        model=args.model,
        max_iters=args.max_iters,
        push=args.push,
        keep_runtime_artifacts=args.keep_runtime_artifacts,
        ledger_path=args.ledger_path,
        metrics_path=args.metrics_path,
        recovery_report_path=args.recovery_report_path,
        supervised_handoff_path=args.supervised_handoff_path,
        resume_state_path=args.resume_state_path,
    )
    entry = dict(result["entry"])
    print(json.dumps(result, indent=2, sort_keys=True))
    decision = str(entry.get("final_decision", "") or "")
    if decision == "completed":
        return 0
    if decision in {"blocked_supervised_only", "escalation_required"}:
        return 2
    validation = dict(entry.get("validation", {}) or {})
    return int(validation.get("returncode", 1) or 1)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
