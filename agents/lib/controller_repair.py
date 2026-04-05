from __future__ import annotations
import re
from typing import Any, Iterable
from agents.lib.controller_contract import (
    CHECKPOINT_TRUTH_FIELDS,
    CONTROLLER_FAILURE_CATEGORIES,
    CONTROLLER_FAILURE_DIGEST_FIELDS,
    CONTROLLER_FAMILY_FILES,
    MERGE_POSTURE_POST_TASK_DECISIONS,
    POLICY_BLOCKED_FAILURE_CATEGORY,
    RESUME_METADATA_FIELDS,
)
_KNOWN_DECISION_STRINGS = {
    "accepted",
    "retryable_failure",
    "manual_patch",
    "blocked",
    "continue",
    "stop",
    "failed_merge",
    "failed_checks",
    "failed_reset",
    "active",
    "completed",
    "failed",
    "resume_same_task",
    "resume_next",
    "resume_after_merge",
    "resume_after_manual_resolution",
}
_CONTROLLER_TAXONOMY_TOKENS = tuple(
    sorted(
        {
            POLICY_BLOCKED_FAILURE_CATEGORY,
            *CONTROLLER_FAILURE_CATEGORIES,
            "seam_contract_mismatch",
            "task_shape_mismatch",
            "file_local_semantic_failure",
            "ci_only_failure",
        }
    )
)
_PYTEST_NAME_RE = re.compile(r"(?m)^(?:_{5,}\s+)?(test_[A-Za-z0-9_]+)")
_ASSERT_MISMATCH_RE = re.compile(r"assert\s+['\"]([^'\"]+)['\"]\s*==\s*['\"]([^'\"]+)['\"]")
_ATTR_MISSING_RE = re.compile(r"has no attribute ['\"]([^'\"]+)['\"]")
_IMPORT_MISSING_SYMBOL_RE = re.compile(r"imports missing symbol ['\"]([^'\"]+)['\"]")
_KEY_ERROR_RE = re.compile(r"KeyError:\s*['\"]([^'\"]+)['\"]")
_PATH_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.(?:py|md))")
_MODULE_ATTR_RE = re.compile(r"module ['\"]([^'\"]+)['\"] has no attribute")
def _normalize_path(path: str) -> str:
    return str(path or "").strip().replace("\\", "/")
def _stable_unique(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        value = str(item or "").strip()
        if value and value not in seen:
            seen.add(value)
            out.append(value)
    return out
def controller_family_files_touched(paths: Iterable[str] | None = None, *, details: str = "") -> list[str]:
    candidates = {_normalize_path(path) for path in (paths or ()) if str(path or "").strip()}
    detail_text = str(details or "")
    for match in _PATH_RE.findall(detail_text):
        candidates.add(_normalize_path(match))
    for module_name in _MODULE_ATTR_RE.findall(detail_text):
        module_path = _normalize_path(str(module_name).replace(".", "/") + ".py")
        candidates.add(module_path)
    return [path for path in CONTROLLER_FAMILY_FILES if path in candidates]
def _decision_mismatches(details: str) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for actual, expected in _ASSERT_MISMATCH_RE.findall(str(details or "")):
        actual_value = str(actual).strip()
        expected_value = str(expected).strip()
        if actual_value in _KNOWN_DECISION_STRINGS or expected_value in _KNOWN_DECISION_STRINGS:
            out.append({"actual": actual_value, "expected": expected_value})
    return out
def _field_presence_drift(details: str) -> tuple[list[str], list[str]]:
    text = str(details or "")
    field_names = tuple(sorted({*CHECKPOINT_TRUTH_FIELDS, *RESUME_METADATA_FIELDS}))
    missing: list[str] = []
    extra: list[str] = []
    lower = text.lower()
    for field in field_names:
        patterns_missing = (
            f"missing persisted truth field '{field}'",
            f'missing persisted truth field "{field}"',
            f"missing truth field '{field}'",
            f'missing truth field "{field}"',
            f"missing required field '{field}'",
            f'missing required field "{field}"',
            f"keyerror: '{field}'".lower(),
            f'keyerror: "{field}"'.lower(),
        )
        if any(pattern in lower for pattern in patterns_missing):
            missing.append(field)
            continue
        if re.search(rf"\bmissing\b[^\n]*\b{re.escape(field)}\b", lower):
            missing.append(field)
            continue
        patterns_extra = (
            f"unexpected persisted truth field '{field}'",
            f'unexpected persisted truth field "{field}"',
            f"extra persisted truth field '{field}'",
            f'extra persisted truth field "{field}"',
            f"unexpected field '{field}'",
            f'unexpected field "{field}"',
        )
        if any(pattern in lower for pattern in patterns_extra):
            extra.append(field)
            continue
        if re.search(rf"\b(?:unexpected|extra)\b[^\n]*\b{re.escape(field)}\b", lower):
            extra.append(field)
    return _stable_unique(missing), _stable_unique(extra)
def _missing_exports(details: str) -> list[str]:
    exports = list(_ATTR_MISSING_RE.findall(str(details or "")))
    exports.extend(_IMPORT_MISSING_SYMBOL_RE.findall(str(details or "")))
    return _stable_unique(exports)
def _merge_posture_mismatches(details: str, decision_mismatches: list[dict[str, str]]) -> list[str]:
    out: list[str] = []
    text = str(details or "")
    for mismatch in decision_mismatches:
        actual = mismatch.get("actual", "")
        expected = mismatch.get("expected", "")
        if actual in MERGE_POSTURE_POST_TASK_DECISIONS or expected in MERGE_POSTURE_POST_TASK_DECISIONS:
            out.append(f"decision drift: actual={actual} expected={expected}")
    if "merge-posture" in text.lower():
        out.append("merge-posture text drift present")
    return _stable_unique(out)
def _taxonomy_mismatches(details: str, category: str) -> list[str]:
    text = str(details or "")
    out: list[str] = []
    for actual, expected in _ASSERT_MISMATCH_RE.findall(text):
        actual_value = str(actual).strip()
        expected_value = str(expected).strip()
        if actual_value in _CONTROLLER_TAXONOMY_TOKENS or expected_value in _CONTROLLER_TAXONOMY_TOKENS:
            out.append(f"taxonomy drift: actual={actual_value} expected={expected_value}")
    if str(category or "").strip() == POLICY_BLOCKED_FAILURE_CATEGORY and "policy" not in text.lower():
        out.append("policy_blocked category without explicit policy context")
    return _stable_unique(out)
def build_controller_failure_digest(
    *,
    kind: str,
    message: str,
    category: str = "",
    touched_files: Iterable[str] | None = None,
    task_file: str = "",
) -> dict[str, Any]:
    text = str(message or "")
    touched = controller_family_files_touched([*(touched_files or ()), task_file], details=text)
    decision_mismatches = _decision_mismatches(text)
    missing_truth_fields, extra_truth_fields = _field_presence_drift(text)
    missing_exports = _missing_exports(text)
    merge_posture_mismatches = _merge_posture_mismatches(text, decision_mismatches)
    taxonomy_mismatches = _taxonomy_mismatches(text, category)
    failing_tests = _stable_unique(_PYTEST_NAME_RE.findall(text))[:12]
    is_controller_failure = bool(
        touched
        or decision_mismatches
        or missing_truth_fields
        or extra_truth_fields
        or missing_exports
        or merge_posture_mismatches
        or taxonomy_mismatches
    )
    digest = {
        "failure_kind": str(kind or "unknown").strip() or "unknown",
        "failure_category": str(category or "").strip(),
        "is_controller_failure": is_controller_failure,
        "failing_tests": failing_tests,
        "decision_mismatches": decision_mismatches,
        "missing_truth_fields": missing_truth_fields,
        "extra_truth_fields": extra_truth_fields,
        "missing_exports": missing_exports,
        "merge_posture_mismatches": merge_posture_mismatches,
        "taxonomy_mismatches": taxonomy_mismatches,
        "controller_family_files_touched": touched,
    }
    return {field: digest[field] for field in CONTROLLER_FAILURE_DIGEST_FIELDS}
def format_controller_failure_digest(digest: dict[str, Any] | None) -> str:
    payload = dict(digest or {})
    if not payload.get("is_controller_failure"):
        return ""
    lines = ["Controller semantic failure digest:"]
    if payload.get("failing_tests"):
        lines.append("- failing_tests: " + ", ".join(str(item) for item in payload["failing_tests"]))
    if payload.get("decision_mismatches"):
        joined = "; ".join(
            f"actual={item.get('actual', '')} expected={item.get('expected', '')}"
            for item in payload["decision_mismatches"]
        )
        lines.append("- decision_mismatches: " + joined)
    if payload.get("missing_truth_fields"):
        lines.append("- missing_truth_fields: " + ", ".join(str(item) for item in payload["missing_truth_fields"]))
    if payload.get("extra_truth_fields"):
        lines.append("- extra_truth_fields: " + ", ".join(str(item) for item in payload["extra_truth_fields"]))
    if payload.get("missing_exports"):
        lines.append("- missing_exports: " + ", ".join(str(item) for item in payload["missing_exports"]))
    if payload.get("merge_posture_mismatches"):
        lines.append("- merge_posture_mismatches: " + "; ".join(str(item) for item in payload["merge_posture_mismatches"]))
    if payload.get("taxonomy_mismatches"):
        lines.append("- taxonomy_mismatches: " + "; ".join(str(item) for item in payload["taxonomy_mismatches"]))
    if payload.get("controller_family_files_touched"):
        lines.append(
            "- controller_family_files_touched: " + ", ".join(str(item) for item in payload["controller_family_files_touched"])
        )
    return "\n".join(lines)
def build_controller_repair_context(
    *,
    kind: str,
    message: str,
    category: str = "",
    touched_files: Iterable[str] | None = None,
    task_file: str = "",
) -> dict[str, Any]:
    digest = build_controller_failure_digest(
        kind=kind,
        message=message,
        category=category,
        touched_files=touched_files,
        task_file=task_file,
    )
    lines = [
        "Focused controller repair required.",
        "Use the semantic failure digest below in addition to the raw failing output.",
        "Repair the named controller surfaces first; do not rely only on stack traces.",
    ]
    if str(task_file or "").strip():
        lines.insert(1, f"Task file: {task_file}")
    formatted_digest = format_controller_failure_digest(digest)
    if formatted_digest:
        lines.append(formatted_digest)
    return {
        "semantic_failure_digest": digest,
        "repair_prompt": "\n".join(lines),
    }
def build_controller_test_failure_appendix(
    *,
    details: str,
    semantic_hints: str = "",
    kind: str = "tests",
    category: str = "tests",
    touched_files: Iterable[str] | None = None,
    task_file: str = "",
) -> str:
    context = build_controller_repair_context(
        kind=kind,
        message=details,
        category=category,
        touched_files=touched_files,
        task_file=task_file,
    )
    controller_repair_prompt = str(context.get("repair_prompt", "")).strip()
    sections = [
        "# Last run failures",
        str(details or "").strip(),
        "IMPORTANT: Fix the reported failures exactly. Modify implementation files to satisfy failing tests. Do not change tests unless the task explicitly requires it. Use exact expected values from pytest output as the source of truth.",
    ]
    semantic_hints = str(semantic_hints or "").strip()
    if semantic_hints:
        sections.extend(["# Failure analysis hints", semantic_hints])
    if controller_repair_prompt:
        sections.extend(["# Controller repair context", controller_repair_prompt])
    return "\n".join(section for section in sections if section).strip()
