from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence


def _normalize_paths(paths: Sequence[object] | None) -> list[str]:
    normalized: list[str] = []
    seen: set[str] = set()
    for raw in paths or ():
        value = str(raw or "").strip().replace("\\", "/")
        if value and value not in seen:
            normalized.append(value)
            seen.add(value)
    return normalized


def _coerce_str_list(value: object) -> list[str]:
    items: list[str] = []
    seen: set[str] = set()
    for raw in value or ():  # type: ignore[arg-type]
        text = str(raw or "").strip()
        if text and text not in seen:
            items.append(text)
            seen.add(text)
    return items


def _combined_output_text(
    *,
    execution_summary: Mapping[str, Any] | None,
    verifier_artifact: Mapping[str, Any] | None,
) -> str:
    execution = dict(execution_summary or {})
    verifier = dict(verifier_artifact or {})
    critique = dict(verifier.get("tester_critique_bundle") or {})
    parts = [
        str(execution.get("stdout_tail", "") or ""),
        str(execution.get("stderr_tail", "") or ""),
        str(verifier.get("failure_message", "") or ""),
        str(verifier.get("validator_note", "") or ""),
        str(critique.get("raw_output_excerpt", "") or ""),
    ]
    return "\n".join(part for part in parts if part).strip()


def _paths_mentioned_in_output(output_text: str, required_paths: Sequence[str]) -> list[str]:
    lower = output_text.lower()
    matches: list[str] = []
    for path in required_paths:
        name = Path(path).name.lower()
        full = path.lower()
        if full in lower or name in lower:
            matches.append(path)
    return matches


def classify_single_task_failure(
    *,
    task_path: str,
    required_paths: Sequence[object] | None = None,
    execution_summary: Mapping[str, Any] | None = None,
    developer_artifact: Mapping[str, Any] | None = None,
    verifier_artifact: Mapping[str, Any] | None = None,
) -> dict[str, object]:
    required = _normalize_paths(
        required_paths
        or dict(developer_artifact or {}).get("required_paths")
        or dict(developer_artifact or {}).get("changed_files")
        or []
    )
    execution = dict(execution_summary or {})
    verifier = dict(verifier_artifact or {})
    critique = dict(verifier.get("tester_critique_bundle") or {})

    verdict = str(verifier.get("verdict") or ("fail" if execution else "not_run")).strip() or "not_run"
    lint_ok = bool(verifier.get("lint_ok", False))
    test_ok = bool(verifier.get("test_ok", False))
    likely_failure_family = str(verifier.get("likely_failure_family") or critique.get("likely_failure_family") or "").strip()
    output_text = _combined_output_text(execution_summary=execution, verifier_artifact=verifier)
    lower = output_text.lower()

    failing_test_files = _coerce_str_list(critique.get("failing_test_files"))
    failing_test_nodes = _coerce_str_list(critique.get("failing_test_nodes"))
    likely_touched_files = _coerce_str_list(critique.get("likely_touched_files"))
    focused_replay_commands = _coerce_str_list(critique.get("focused_replay_commands") or verifier.get("focused_results"))
    broad_replay_commands = _coerce_str_list(critique.get("broad_replay_commands") or verifier.get("full_results"))
    output_path_matches = _paths_mentioned_in_output(output_text, required)

    failure_family = "pass" if verdict == "pass" else "blocked" if verdict == "blocked" else "unknown"
    failure_category = "none" if verdict == "pass" else "blocked" if verdict == "blocked" else "unknown"
    self_heal_lane = "none" if verdict in {"pass", "blocked"} else "supervised_recovery"
    smallest_credible_action = (
        "No failure classification required because the bounded verifier passed."
        if verdict == "pass"
        else "No autonomous self-heal action was selected because the task never entered bounded execution."
        if verdict == "blocked"
        else "Escalate to supervised recovery because no narrow external-safe failure family matched."
    )
    self_heal_reason = smallest_credible_action
    matched_signals: list[str] = []
    confidence = "low"
    evidence_paths: list[str] = []

    if verdict == "fail":
        if any(token in lower for token in ("missing deliverable", "missing required deliverable")) or bool(
            execution.get("missing_deliverable_retry_observed", False)
        ):
            failure_family = "incomplete_deliverable_coverage"
            failure_category = "deliverable_coverage"
            self_heal_lane = "deliverable_patch_only"
            smallest_credible_action = "Patch the explicitly missing required deliverable paths before any broader replay."
            self_heal_reason = "Verifier evidence points to missing deliverable coverage, so the narrowest credible self-heal is to complete the omitted required paths first."
            matched_signals = ["missing_deliverable_signal"]
            confidence = "high"
            evidence_paths = list(required)
        elif (
            "modulenotfounderror" in lower
            or "importerror" in lower
            or "cannot import name" in lower
            or "import file mismatch" in lower
            or likely_failure_family == "import_contract"
            or ("collected 0 items" in lower and "error" in lower)
        ):
            failure_family = "import_collection_error"
            failure_category = "import_collection"
            self_heal_lane = "focused_import_collection_repair"
            smallest_credible_action = "Replay the smallest failing import/collection target first and patch only the implicated import surface."
            self_heal_reason = "Verifier evidence points to import or collection failure, so the smallest credible self-heal is a focused import/collection repair."
            matched_signals = ["import_collection_signal"]
            confidence = "high"
            evidence_paths = failing_test_files or output_path_matches or likely_touched_files[:2] or required[:2]
        elif output_path_matches and any(
            token in lower for token in ("filenotfounderror", "no such file or directory", "can't open file", "could not read", "unable to open")
        ):
            failure_family = "missing_file_updates"
            failure_category = "required_path_missing"
            self_heal_lane = "required_path_patch_only"
            smallest_credible_action = "Patch the missing required file updates directly before widening replay."
            self_heal_reason = "Verifier evidence references an expected required path that is missing or unreadable, so the narrowest self-heal is a direct required-path patch."
            matched_signals = ["required_path_missing_signal"]
            confidence = "high"
            evidence_paths = output_path_matches
        elif (not lint_ok) and (test_ok or (not failing_test_files and not failing_test_nodes and "ruff" in lower)):
            failure_family = "formatting_lint_only"
            failure_category = "lint_only"
            self_heal_lane = "lint_only_repair"
            smallest_credible_action = "Repair lint or formatting findings only, rerun lint, and only then widen validation if still needed."
            self_heal_reason = "Verifier evidence isolates the failure to lint/formatting, so the self-heal should stay in a lint-only repair lane."
            matched_signals = ["lint_only_signal"]
            confidence = "high"
            evidence_paths = likely_touched_files[:3] or required[:3]
        elif (not test_ok) and (lint_ok or failing_test_files or failing_test_nodes or likely_failure_family in {"result_shape", "docs_drift"}):
            failure_family = "test_regression"
            failure_category = "tests"
            self_heal_lane = "focused_test_repair"
            smallest_credible_action = "Replay the narrowest failing test target first and patch only the implicated regression surface."
            self_heal_reason = "Verifier evidence shows a bounded test regression, so the narrowest self-heal is a focused test replay followed by a targeted patch."
            matched_signals = ["test_regression_signal"]
            confidence = "high" if failing_test_files or failing_test_nodes else "medium"
            evidence_paths = failing_test_files[:3] or likely_touched_files[:3] or required[:3]

    return {
        "schema_version": 1,
        "task_path": str(task_path or ""),
        "verdict": verdict,
        "failure_family": failure_family,
        "failure_category": failure_category,
        "likely_failure_family": likely_failure_family,
        "self_heal_lane": self_heal_lane,
        "smallest_credible_action": smallest_credible_action,
        "self_heal_reason": self_heal_reason,
        "confidence": confidence,
        "matched_signals": matched_signals,
        "required_paths": list(required),
        "evidence_paths": list(evidence_paths),
        "failing_test_files": list(failing_test_files),
        "failing_test_nodes": list(failing_test_nodes),
        "likely_touched_files": list(likely_touched_files),
        "focused_replay_commands": list(focused_replay_commands),
        "broad_replay_commands": list(broad_replay_commands),
        "raw_output_excerpt": output_text[-1200:],
    }


__all__ = ["classify_single_task_failure"]
