from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from agents.lib.check_runner import build_ordinary_task_execution_plan, build_tester_critique_bundle
from agents.lib.multi_agent_contract import canonical_role_artifact_envelope


def _dedupe_paths(paths: Sequence[object] | None) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for raw in paths or ():
        value = str(raw or "").strip().replace("\\", "/")
        if value and value not in seen:
            ordered.append(value)
            seen.add(value)
    return ordered


def build_single_task_developer_artifact(
    *,
    task_path: str,
    required_paths: Sequence[object] | None,
    command: Sequence[object] | None,
    execution_summary: Mapping[str, Any] | None,
    execution_invoked: bool,
) -> dict[str, object]:
    execution = dict(execution_summary or {})
    role_outcome = "builder_patch_proposed" if execution_invoked else "builder_noop"
    summary = (
        "Developer invoked the bounded one-task generation lane and returned candidate changes for verification."
        if execution_invoked
        else "Developer generation was not invoked because the task stayed outside the admitted autonomous lane."
    )
    changed_files = _dedupe_paths(required_paths)
    raw_payload = {
        "role": "builder",
        "artifact_kind": "single_task_developer_artifact",
        "task_path": str(task_path or ""),
        "task_name": Path(str(task_path or "")).name,
        "execution_invoked": bool(execution_invoked),
        "command": [str(part) for part in (command or execution.get("command") or [])],
        "changed_files": changed_files,
        "required_paths": changed_files,
        "observed_iterations": int(execution.get("observed_iterations", 0) or 0),
        "configured_max_iters": int(execution.get("configured_max_iters", 0) or 0),
        "retry_count_observed": int(execution.get("retry_count_observed", 0) or 0),
        "stdout_tail": str(execution.get("stdout_tail", "") or ""),
        "stderr_tail": str(execution.get("stderr_tail", "") or ""),
        "summary": summary,
        "role_outcome": role_outcome,
        "proposed_next_role": "verifier",
    }
    envelope = canonical_role_artifact_envelope(
        raw_payload,
        envelope_type="coder_output",
        artifact_role="builder",
        task_path=str(task_path or ""),
        attempt_count=max(1, int(execution.get("observed_iterations", 0) or 0) or 1),
        summary=summary,
        role_outcome=role_outcome,
        proposed_next_role="verifier",
        handoff_reason="developer_finished_generation",
        handoff_summary=summary,
        handoff_instructions="Route the candidate change set to the verifier for focused and broad validation.",
        changed_files=changed_files,
    )
    raw_payload["artifact_envelope"] = envelope
    return raw_payload


def build_single_task_verifier_artifact(
    *,
    task_path: str,
    developer_artifact: Mapping[str, Any] | None,
    execution_summary: Mapping[str, Any] | None,
    execution_invoked: bool,
) -> dict[str, object]:
    developer = dict(developer_artifact or {})
    execution = dict(execution_summary or {})
    lint_ok = bool(execution_invoked and execution.get("ruff_green_observed", False))
    test_ok = bool(execution_invoked and execution.get("pytest_green_observed", False))
    output_text = "\n".join(
        [
            str(execution.get("stdout_tail", "") or ""),
            str(execution.get("stderr_tail", "") or ""),
        ]
    ).strip()
    critique = build_tester_critique_bundle(
        {
            "lint_ok": lint_ok,
            "test_ok": test_ok,
            "output_text": output_text,
            "changed_files": developer.get("changed_files", []),
        }
    )
    execution_plan = build_ordinary_task_execution_plan(
        {
            "lint_ok": lint_ok,
            "test_ok": test_ok,
            "output_text": output_text,
            "changed_files": developer.get("changed_files", []),
            "tester_critique_bundle": critique,
        },
        task_context={"task_admission_lane": "autonomous_ordinary"},
        changed_files=developer.get("changed_files", []),
    )
    if lint_ok and test_ok:
        verdict = "pass"
        acceptance_decision = "accepted"
        post_task_decision = "continue"
        next_task_may_proceed = True
        summary = "Verifier observed green focused/full validation evidence for the bounded one-task run."
        role_outcome = "verification_passed"
    elif execution_invoked:
        verdict = "fail"
        acceptance_decision = "retryable_failure"
        post_task_decision = "stop"
        next_task_may_proceed = False
        summary = "Verifier produced failing evidence and a bounded critique bundle for targeted repair selection."
        role_outcome = "verification_failed"
    else:
        verdict = "blocked"
        acceptance_decision = "blocked"
        post_task_decision = "stop"
        next_task_may_proceed = False
        summary = "Verifier did not run because the bounded one-task developer lane was not invoked."
        role_outcome = "verification_blocked"

    acceptance_report = {
        "acceptance_decision": acceptance_decision,
        "post_task_decision": post_task_decision,
        "next_task_may_proceed": next_task_may_proceed,
        "note": summary,
        "failure_category": str(critique.get("failure_category") or critique.get("likely_failure_family") or ""),
    }
    focused_results = list(critique.get("focused_replay_commands") or [])
    full_results = list(critique.get("broad_replay_commands") or [])
    raw_payload = {
        "role": "verifier",
        "artifact_kind": "single_task_verifier_artifact",
        "task_path": str(task_path or ""),
        "validator_ok": bool(lint_ok and test_ok),
        "lint_ok": lint_ok,
        "test_ok": test_ok,
        "verdict": verdict,
        "summary": summary,
        "validator_note": str(critique.get("critique_summary") or summary),
        "focused_results": focused_results,
        "full_results": full_results,
        "tester_critique_bundle": critique,
        "tester_execution_plan": execution_plan,
        "acceptance_report": acceptance_report,
        "likely_failure_family": str(critique.get("likely_failure_family") or ""),
        "failure_category": str(critique.get("failure_category") or critique.get("likely_failure_family") or ""),
        "failure_message": str(critique.get("critique_summary") or ""),
        "role_outcome": role_outcome,
        "proposed_next_role": "controller" if verdict == "pass" else "repair",
        "verification_authority_profile": "local_only",
        "verification_authority_satisfied": bool(lint_ok and test_ok),
        "focused_validation_commands": focused_results,
        "full_validation_commands": full_results,
    }
    envelope = canonical_role_artifact_envelope(
        raw_payload,
        envelope_type="tester_output",
        artifact_role="verifier",
        task_path=str(task_path or ""),
        attempt_count=max(1, int(developer.get("observed_iterations", 0) or 0) or 1),
        summary=summary,
        role_outcome=role_outcome,
        proposed_next_role="controller" if verdict == "pass" else "repair",
        handoff_reason="verifier_completed_validation",
        handoff_summary=summary,
        handoff_instructions="Route verifier evidence to repair selection when failing, otherwise to controller acceptance.",
        verifier_verdict=verdict,
        acceptance_decision=acceptance_decision,
        post_task_decision=post_task_decision,
        next_task_may_proceed=next_task_may_proceed,
        changed_files=developer.get("changed_files", []),
        focused_result_count=len(focused_results),
        full_result_count=len(full_results),
        verification_authority_profile="local_only",
    )
    raw_payload["artifact_envelope"] = envelope
    return raw_payload


__all__ = [
    "build_single_task_developer_artifact",
    "build_single_task_verifier_artifact",
]
