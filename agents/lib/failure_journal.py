from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

from agents.lib.controller_contract import POLICY_BLOCKED_FAILURE_CATEGORY
from agents.lib.controller_repair import build_controller_failure_digest, build_controller_repair_context

DEFAULT_RAW_SNIPPET_LIMIT = 400
DEFAULT_JOURNAL_PATH = Path("artifacts/failure_journal.jsonl")
_FAILURE_COUNTS: Dict[str, int] = {}


def classify_failure(kind: str, message: str) -> str:
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
    if "github actions" in text or "required status check" in text or "workflow" in text or re.search(r"\bci\b", text):
        return "ci_only_failure"
    if any(token in text for token in ("controller strict mode", "patch-quality gate", "low-discipline generated patch", "compressed multi-import", "semicolon density")):
        return "controller_patch_quality"
    if any(token in text for token in ("semantic", "unknown export key", "non-live failure-journal", "file-local semantic")):
        return "file_local_semantic_failure"
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
    value = re.sub(r'"[^"]*"', "\"<value>\"", value)
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
    plans: Dict[str, Dict[str, Any]] = {
        "python_syntax": dict(recommended_next_action="retry_with_targeted_fix", chosen_remediation_path="targeted_syntax_repair", autonomy_confidence=0.95, continue_autonomously=True, manual_lane_recommended=False),
        "file_local_semantic_failure": dict(recommended_next_action="localized_repair", chosen_remediation_path="file_local_semantic_repair", autonomy_confidence=0.82, continue_autonomously=True, manual_lane_recommended=False),
        "controller_patch_quality": dict(recommended_next_action="retry_with_targeted_fix", chosen_remediation_path="controller_patch_quality_repair", autonomy_confidence=0.40, continue_autonomously=True, manual_lane_recommended=False),
        "task_shape_mismatch": dict(recommended_next_action="patch_task_contract", chosen_remediation_path="task_shape_patch", autonomy_confidence=0.38, continue_autonomously=False, manual_lane_recommended=False),
        "seam_contract_mismatch": dict(recommended_next_action="patch_runner_or_task_contract", chosen_remediation_path="semantic_contract_repair", autonomy_confidence=0.30, continue_autonomously=False, manual_lane_recommended=False),
        "harness_meta_regression": dict(recommended_next_action="manual_patch", chosen_remediation_path="manual_patch_lane", autonomy_confidence=0.10, continue_autonomously=False, manual_lane_recommended=True),
        "policy_blocked": dict(recommended_next_action="manual_patch", chosen_remediation_path="manual_patch_lane", autonomy_confidence=0.10, continue_autonomously=False, manual_lane_recommended=True),
        "ci_only_failure": dict(recommended_next_action="retry_with_targeted_fix", chosen_remediation_path="ci_only_repair", autonomy_confidence=0.55, continue_autonomously=False, manual_lane_recommended=False),
    }
    plan = dict(plans.get(category, dict(recommended_next_action="retry_with_targeted_fix", chosen_remediation_path="targeted_retry", autonomy_confidence=0.50, continue_autonomously=False, manual_lane_recommended=False)))
    if retry_count >= 3:
        plan.update(dict(recommended_next_action="manual_patch", chosen_remediation_path="manual_patch_lane", autonomy_confidence=0.0, continue_autonomously=False, manual_lane_recommended=True))
    plan.update(dict(failure_category=category, retry_count=retry_count, failure_fingerprint=fingerprint, raw_failure_snippet=raw_failure_snippet))
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
    return {
        "task_path": str(task_path),
        "role_trace": list(role_trace),
        "builder_summary": str((builder_artifact or {}).get("summary") or ""),
        "verifier_summary": str((verifier_artifact or {}).get("summary") or ""),
        "controller_summary": str((controller_decision or {}).get("summary") or ""),
        "verifier_verdict": str((verifier_artifact or {}).get("verdict") or "not_run"),
        "controller_action": str((controller_decision or {}).get("action") or ""),
        "final_authority_role": str((controller_decision or {}).get("final_authority_role") or "controller"),
    }
