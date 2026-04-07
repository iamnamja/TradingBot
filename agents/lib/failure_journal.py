from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from agents.lib.controller_contract import POLICY_BLOCKED_FAILURE_CATEGORY
from agents.lib.check_runner import summarize_tester_critique_bundle
from agents.lib.multi_agent_contract import summarize_role_artifact_envelope
from agents.lib.controller_repair import (
    build_controller_failure_digest,
    build_controller_repair_context,
    build_repair_attempt_record,
    choose_repair_strategy,
    classify_collection_failure,
    evaluate_repair_attempt_memory,
    repair_attempt_fingerprint,
)

DEFAULT_RAW_SNIPPET_LIMIT = 400
DEFAULT_JOURNAL_PATH = Path("artifacts/failure_journal.jsonl")
_FAILURE_COUNTS: Dict[str, int] = {}


def classify_failure(kind: str, message: str) -> str:
    collection_category = classify_collection_failure(kind=kind, message=message)
    if collection_category:
        return collection_category
    text = f"{kind}\n{message}".lower()
    if "modulenotfounderror" in text or "imports" in text:
        return "imports"
    if "syntaxerror" in text or "python syntax" in text or "invalid syntax" in text or "unterminated string literal" in text:
        return "python_syntax"
    if any(token in text for token in ("failure_journal_export", "shell_router_export", "validator_runner_exports", "_validator_runner_exports", "seam manifest", "semantic contract")):
        return "seam_contract_mismatch"
    if any(token in text for token in ("protected meta", "normal bundle lane", "protected-file method mode", "meta harness")):
        return POLICY_BLOCKED_FAILURE_CATEGORY
    if any(token in text for token in ("required file", "unexpected file", "deliverable", "task shape", "material update", "split recommendation")):
        return "task_shape_mismatch"
    if any(token in text for token in ("bootstrap", "environment", "venv", "pip install", "missing executable", "toolchain", "no such file or directory")):
        return "environment_setup_failure"
    if "github actions" in text or "required status check" in text or "workflow" in text or re.search(r"\bci\b", text):
        return "ci_only_failure"
    if any(token in text for token in ("controller strict mode", "patch-quality gate", "low-discipline generated patch", "compressed multi-import", "semicolon density")):
        return "controller_patch_quality"
    if any(token in text for token in ("semantic", "unknown export key", "non-live failure-journal", "file-local semantic")):
        return "file_local_semantic_failure"
    if any(token in text for token in ("proof-claim", "proof claim", "docs/", "readme", "documentation claim", "status narrative")):
        return "docs_proof_claim_drift"
    if "ruff" in text or "lint" in text:
        return "lint"
    if "bundle" in text or "end_file" in text or "begin_file_bundle" in text:
        return "bundle_transport"
    if "policy" in text:
        return "policy_violation"
    if "pytest" in text or "assert " in text or "test_" in text:
        return "tests"
    return (kind or "unknown").strip() or "unknown"


def _normalize_failure_message(message: str) -> str:
    value = str(message or "")
    value = re.sub(r"'[^']*'", "'<value>'", value)
    value = re.sub(r'"[^"]*"', '"<value>"', value)
    value = re.sub(r"\b\d+\b", "<num>", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def failure_fingerprint(*, kind: str, message: str, category: str) -> str:
    payload = f"{category}|{kind}|{_normalize_failure_message(message)}".encode("utf-8", errors="replace")
    digest = hashlib.sha1(payload).hexdigest()[:12]
    return f"{category}:{digest}"


def bounded_failure_snippet(message: str, max_chars: int = DEFAULT_RAW_SNIPPET_LIMIT) -> str:
    value = str(message or "")
    limit = max(32, int(max_chars))
    if len(value) <= limit:
        return value
    suffix = "...[truncated]"
    head = value[: max(0, limit - len(suffix))]
    return f"{head}{suffix}"


def build_failure_remediation_plan(*, kind: str, message: str, category: str, retry_count: int, fingerprint: str, raw_failure_snippet: str) -> Dict[str, Any]:
    route = choose_repair_strategy(kind=kind, message=message, category=category)
    recommended = "manual_patch"
    if route["remediation_lane"] == "builder":
        recommended = "retry_with_targeted_fix"
    elif route["remediation_lane"] == "verifier":
        recommended = "rerun_verifier_lane"
    plan = {
        "recommended_next_action": recommended,
        "chosen_remediation_path": str(route["repair_strategy"]),
        "repair_strategy": str(route["repair_strategy"]),
        "remediation_lane": str(route["remediation_lane"]),
        "autonomy_confidence": 0.0,
        "continue_autonomously": bool(route["continue_autonomously"]),
        "manual_lane_recommended": bool(route["manual_lane_recommended"]),
        "failure_category": category,
        "retry_count": retry_count,
        "failure_fingerprint": fingerprint,
        "raw_failure_snippet": raw_failure_snippet,
        "route_rationale": str(route.get("route_rationale") or route["rationale"]),
        "targeted_patch_surface": str(route.get("targeted_patch_surface") or "broad_builder_repair"),
        "target_files": [str(item) for item in route.get("target_files") or [] if str(item)],
        "prefer_minimal_patch": bool(route.get("prefer_minimal_patch", False)),
        "minimal_patch_selected": bool(route.get("minimal_patch_selected", False)),
        "max_files_to_edit": int(route.get("max_files_to_edit", 0)),
    }
    repair_attempt = build_repair_attempt_record(
        task_path="",
        repair_strategy=str(plan["repair_strategy"]),
        targeted_patch_surface=str(plan["targeted_patch_surface"]),
        target_files=plan["target_files"],
        failure_fingerprint=fingerprint,
        retry_count=retry_count,
    )
    plan["repair_attempt_fingerprint"] = str(repair_attempt["repair_attempt_fingerprint"])
    plan["repair_target_files"] = list(repair_attempt["target_files"])
    plan["repair_target_surface"] = str(repair_attempt["targeted_patch_surface"])
    if plan["remediation_lane"] == "builder":
        plan["autonomy_confidence"] = 0.8 if retry_count <= 2 else 0.35
    elif plan["remediation_lane"] == "verifier":
        plan["autonomy_confidence"] = 0.7 if retry_count <= 2 else 0.25
    if retry_count >= 3 and plan["remediation_lane"] != "verifier":
        plan.update(
            recommended_next_action="manual_patch",
            chosen_remediation_path="manual_stop",
            repair_strategy="manual_stop",
            remediation_lane="operator",
            autonomy_confidence=0.0,
            continue_autonomously=False,
            manual_lane_recommended=True,
            route_rationale="Repeated failures exhausted the conservative autonomous repair budget.",
            targeted_patch_surface="manual_stop",
            target_files=[],
            prefer_minimal_patch=False,
            minimal_patch_selected=False,
            max_files_to_edit=0,
        )
    return plan


def recommended_next_action(*, kind: str, message: str, category: str, retry_count: int, fingerprint: str, raw_failure_snippet: str) -> str:
    return str(build_failure_remediation_plan(kind=kind, message=message, category=category, retry_count=retry_count, fingerprint=fingerprint, raw_failure_snippet=raw_failure_snippet)["recommended_next_action"])


def chosen_remediation_path(*, kind: str, message: str, category: str, retry_count: int, fingerprint: str, raw_failure_snippet: str, recommended_next_action: str) -> str:
    return str(build_failure_remediation_plan(kind=kind, message=message, category=category, retry_count=retry_count, fingerprint=fingerprint, raw_failure_snippet=raw_failure_snippet)["chosen_remediation_path"])


def autonomy_confidence(*, kind: str, message: str, category: str, retry_count: int, fingerprint: str, raw_failure_snippet: str) -> float:
    return float(build_failure_remediation_plan(kind=kind, message=message, category=category, retry_count=retry_count, fingerprint=fingerprint, raw_failure_snippet=raw_failure_snippet)["autonomy_confidence"])


def continue_autonomously(*, kind: str, message: str, category: str, retry_count: int, fingerprint: str, raw_failure_snippet: str) -> bool:
    return bool(build_failure_remediation_plan(kind=kind, message=message, category=category, retry_count=retry_count, fingerprint=fingerprint, raw_failure_snippet=raw_failure_snippet)["continue_autonomously"])


def retry_count_for_fingerprint(fingerprint: str) -> int:
    count = int(_FAILURE_COUNTS.get(fingerprint, 0)) + 1
    _FAILURE_COUNTS[fingerprint] = count
    return count




def collection_failure_category(kind: str, message: str, category: str = "") -> str:
    return str(classify_collection_failure(kind=kind, message=message, category=category))

def build_semantic_failure_digest(*, kind: str, message: str, category: str = "", touched_files: list[str] | None = None, task_file: str = "") -> Dict[str, Any]:
    return dict(
        build_controller_failure_digest(
            kind=kind,
            message=message,
            category=category,
            touched_files=touched_files,
            task_file=task_file,
        )
    )


def build_semantic_repair_context(*, kind: str, message: str, category: str = "", touched_files: list[str] | None = None, task_file: str = "") -> Dict[str, Any]:
    return dict(
        build_controller_repair_context(
            kind=kind,
            message=message,
            category=category,
            touched_files=touched_files,
            task_file=task_file,
        )
    )


def failure_journal_path() -> Path:
    raw = os.getenv("TRADINGBOT_FAILURE_JOURNAL_PATH", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_JOURNAL_PATH


def append_failure_journal_entry(entry: Dict[str, Any], journal_path: Path | str | None = None) -> None:
    path = Path(journal_path) if journal_path is not None else failure_journal_path()
    payload = dict(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def read_failure_journal(journal_path: Path | str | None = None) -> List[Dict[str, Any]]:
    path = Path(journal_path) if journal_path is not None else failure_journal_path()
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def build_multi_agent_failure_context(
    *,
    task_path: str,
    role_trace: list[str] | tuple[str, ...],
    builder_artifact: Dict[str, Any] | dict[str, Any],
    verifier_artifact: Dict[str, Any] | dict[str, Any],
    controller_decision: Dict[str, Any] | dict[str, Any],
) -> Dict[str, Any]:
    coder_summary = summarize_role_artifact_envelope(builder_artifact, envelope_type="coder_output", artifact_role="builder")
    tester_summary = summarize_role_artifact_envelope(verifier_artifact, envelope_type="tester_output", artifact_role="verifier")
    controller_summary = summarize_role_artifact_envelope(
        controller_decision,
        envelope_type="controller_output",
        artifact_role="controller",
    )
    critique_summary = summarize_tester_critique_bundle((verifier_artifact or {}).get("tester_critique_bundle"), failure_message=(verifier_artifact or {}).get("failure_message"), failure_category=(verifier_artifact or {}).get("failure_category"), focused_results=(verifier_artifact or {}).get("focused_results"), full_results=(verifier_artifact or {}).get("full_results"), changed_files=(builder_artifact or {}).get("changed_files"))
    return {
        "task_path": str(task_path),
        "role_trace": list(role_trace),
        "builder_summary": str(coder_summary.get("summary") or ""),
        "verifier_summary": str(tester_summary.get("summary") or ""),
        "controller_summary": str(controller_summary.get("summary") or ""),
        "coder_artifact_summary": coder_summary,
        "tester_artifact_summary": tester_summary,
        "controller_artifact_summary": controller_summary,
        "tester_critique_summary": critique_summary,
        "focused_replay_commands": list(critique_summary.get("focused_replay_commands") or []),
        "broad_replay_commands": list(critique_summary.get("broad_replay_commands") or []),
        "likely_touched_files": list(critique_summary.get("likely_touched_files") or []),
        "verifier_verdict": str(tester_summary.get("verifier_verdict") or "not_run"),
        "controller_action": str((controller_decision or {}).get("action") or ""),
        "repair_strategy": str((controller_decision or {}).get("repair_strategy") or ""),
        "remediation_lane": str((controller_decision or {}).get("remediation_lane") or ""),
        "final_authority_role": str((controller_decision or {}).get("final_authority_role") or "controller"),
    }

__all__ = [
    "evaluate_repair_attempt_memory",
    "repair_attempt_fingerprint",
]
