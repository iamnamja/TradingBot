from __future__ import annotations

import hashlib
import json
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
            "environment_setup_failure",
            "docs_proof_claim_drift",
        }
    )
)

REPAIR_LANES = ("builder", "verifier", "operator")
REPAIR_STRATEGIES = (
    "collection_import_contract_repair",
    "syntax_import_lint_repair",
    "behavioral_test_repair",
    "controller_contract_repair",
    "environment_setup_triage",
    "ci_verification_recheck",
    "docs_proof_claim_repair",
    "manual_stop",
)


def build_repair_attempt_record(
    *,
    task_path: str,
    repair_strategy: str,
    targeted_patch_surface: str,
    target_files: Iterable[str] | None = None,
    failure_fingerprint: str = "",
    retry_count: int = 0,
) -> dict[str, Any]:
    normalized_files = _stable_unique(_normalize_path(path) for path in (target_files or ()) if str(path or "").strip())
    payload = {
        "task_path": str(task_path or "").strip(),
        "repair_strategy": str(repair_strategy or "manual_stop").strip() or "manual_stop",
        "targeted_patch_surface": str(targeted_patch_surface or "manual_stop").strip() or "manual_stop",
        "target_files": normalized_files,
        "failure_fingerprint": str(failure_fingerprint or "").strip(),
    }
    digest = hashlib.sha1(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8", errors="replace")
    ).hexdigest()[:12]
    return {
        **payload,
        "retry_count": max(0, int(retry_count)),
        "repair_attempt_fingerprint": f"repair:{digest}",
    }


def repair_attempt_fingerprint(
    *,
    task_path: str,
    repair_strategy: str,
    targeted_patch_surface: str,
    target_files: Iterable[str] | None = None,
    failure_fingerprint: str = "",
) -> str:
    return str(
        build_repair_attempt_record(
            task_path=task_path,
            repair_strategy=repair_strategy,
            targeted_patch_surface=targeted_patch_surface,
            target_files=target_files,
            failure_fingerprint=failure_fingerprint,
        )["repair_attempt_fingerprint"]
    )


def evaluate_repair_attempt_memory(
    *,
    current_attempt: dict[str, Any] | None,
    prior_attempts: Iterable[dict[str, Any]] | None = None,
    retry_budget: int = 0,
) -> dict[str, Any]:
    attempt = dict(current_attempt or {})
    normalized_prior = [dict(item) for item in (prior_attempts or ()) if isinstance(item, dict)]
    fingerprint = str(attempt.get("repair_attempt_fingerprint") or "").strip()
    duplicate_count = sum(
        1
        for item in normalized_prior
        if str(item.get("repair_attempt_fingerprint") or "").strip() == fingerprint and fingerprint
    )
    same_surface_count = sum(
        1
        for item in normalized_prior
        if str(item.get("repair_strategy") or "").strip() == str(attempt.get("repair_strategy") or "").strip()
        and str(item.get("targeted_patch_surface") or "").strip() == str(attempt.get("targeted_patch_surface") or "").strip()
        and [str(path) for path in item.get("target_files") or []] == [str(path) for path in attempt.get("target_files") or []]
    )
    suppressed = duplicate_count > 0
    no_progress_signal = "duplicate_no_progress_repair_plan" if suppressed else ""
    return {
        "repair_attempt_fingerprint": fingerprint,
        "duplicate_attempt_count": duplicate_count + (1 if fingerprint else 0),
        "same_surface_attempt_count": same_surface_count + 1,
        "retry_budget": max(0, int(retry_budget)),
        "retry_budget_remaining": max(0, int(retry_budget) - duplicate_count),
        "duplicate_attempt_suppressed": suppressed,
        "no_progress_detected": suppressed,
        "repair_memory_signal": no_progress_signal,
        "should_stop": suppressed,
    }


TARGETED_PATCH_SURFACES = (
    "compatibility_alias_only",
    "import_line_only",
    "result_shape_adapter",
    "manifest_schema_adapter",
    "docs_claim_sync",
    "controller_contract_surface",
    "broad_builder_repair",
    "manual_stop",
)


def _target_files_for_surface(surface: str, *, task_file: str = "", touched_files: Iterable[str] | None = None) -> list[str]:
    candidates = _stable_unique([*(touched_files or ()), task_file])
    normalized = [path for path in candidates if path]
    if surface == "docs_claim_sync":
        docs = [path for path in normalized if path.endswith('.md')]
        return docs or [path for path in normalized if '/docs/' in path or path.startswith('docs/')] or [task_file] if task_file else []
    if surface in {"compatibility_alias_only", "result_shape_adapter", "manifest_schema_adapter", "controller_contract_surface"}:
        py_files = [path for path in normalized if path.endswith('.py')]
        return py_files[:4]
    if surface == "import_line_only":
        py_files = [path for path in normalized if path.endswith('.py')]
        return py_files[:2]
    return normalized[:6]


def infer_targeted_repair_surface(
    *,
    kind: str,
    message: str,
    category: str = "",
    touched_files: Iterable[str] | None = None,
    task_file: str = "",
) -> dict[str, Any]:
    text = _coerce_failure_text(kind, message, category)
    normalized_category = str(category or "").strip()
    surface = "broad_builder_repair"
    rationale = "Failure likely requires a broader builder repair surface."
    prefer_minimal = False
    max_files_to_edit = 6

    if classify_collection_failure(kind=kind, message=message, category=normalized_category):
        if any(token in text for token in ("cannot import name", "has no attribute", "unexpected keyword argument", "attributeerror", "keyerror")):
            surface = "compatibility_alias_only"
            rationale = "Collection/import drift points to a narrow compatibility alias or public-surface repair."
            prefer_minimal = True
            max_files_to_edit = 2
        else:
            surface = "import_line_only"
            rationale = "Collection/import drift points to a narrow import or symbol-surface repair."
            prefer_minimal = True
            max_files_to_edit = 2
    elif normalized_category == "bundle_empty_response":
        surface = "bundle_empty_response"
        rationale = "Zero-file bundle responses should retry with a narrow empty-bundle recovery prompt before broader edits."
        prefer_minimal = True
        max_files_to_edit = 0
    elif normalized_category == "bundle_underfilled_response":
        surface = "bundle_missing_deliverables"
        rationale = "Underfilled bundles should retry against the missing requested deliverables rather than broad builder rewrites."
        prefer_minimal = True
        max_files_to_edit = 2
    elif normalized_category in {"bundle_markerless_transport", "bundle_malformed_transport", "imports", "python_syntax", "lint", "bundle_transport"}:
        surface = "bundle_transport_format" if normalized_category in {"bundle_markerless_transport", "bundle_malformed_transport", "bundle_transport"} else "import_line_only"
        rationale = "Import/lint/syntax and malformed transport failures should start with the smallest plausible repair surface."
        prefer_minimal = True
        max_files_to_edit = 2 if surface == "import_line_only" else 0
    elif normalized_category in {"tests", "behavioral_regression"} and any(token in text for token in ("processed_task_ids", "verification_authority", "controller_final_decision", "runtime_portability_scope", "count", "unexpected keyword argument", "task_path", "path")):
        if any(token in text for token in ("task_path", "missing `path`", "path")):
            surface = "manifest_schema_adapter"
            rationale = "The failure looks like bounded manifest-schema drift that should be repaired with a narrow adapter."
        else:
            surface = "result_shape_adapter"
            rationale = "The failure looks like bounded result-shape drift that should be repaired with a narrow adapter."
        prefer_minimal = True
        max_files_to_edit = 3
    elif normalized_category in {"seam_contract_mismatch", "controller_patch_quality", "file_local_semantic_failure"}:
        surface = "controller_contract_surface"
        rationale = "Controller-contract drift should prefer the smallest controller-surface correction before broader rewrites."
        prefer_minimal = True
        max_files_to_edit = 3
    elif normalized_category == "docs_proof_claim_drift":
        surface = "docs_claim_sync"
        rationale = "Docs/proof drift should prefer a narrow documentation sync rather than broader code edits."
        prefer_minimal = True
        max_files_to_edit = 3
    elif normalized_category == POLICY_BLOCKED_FAILURE_CATEGORY or normalized_category == 'environment_setup_failure':
        surface = "manual_stop"
        rationale = "This failure is not safely narrow and should remain manual/operator handled."
        prefer_minimal = False
        max_files_to_edit = 0

    target_files = _target_files_for_surface(surface, task_file=task_file, touched_files=touched_files)
    return {
        "targeted_patch_surface": surface,
        "prefer_minimal_patch": prefer_minimal,
        "max_files_to_edit": max_files_to_edit,
        "target_files": target_files,
        "minimal_patch_reason": rationale,
        "minimal_patch_selected": prefer_minimal and surface != "broad_builder_repair",
    }

_PYTEST_NAME_RE = re.compile(r"(?m)^(?:_{5,}\s+)?(test_[A-Za-z0-9_]+)")
_ASSERT_MISMATCH_RE = re.compile(r"assert\s+['\"]([^'\"]+)['\"]\s*==\s*['\"]([^'\"]+)['\"]")
_ATTR_MISSING_RE = re.compile(r"has no attribute ['\"]([^'\"]+)['\"]")
_IMPORT_MISSING_SYMBOL_RE = re.compile(r"imports missing symbol ['\"]([^'\"]+)['\"]")
_PATH_RE = re.compile(r"([A-Za-z0-9_./\\-]+\.(?:py|md))")
_MODULE_ATTR_RE = re.compile(r"module ['\"]([^'\"]+)['\"] has no attribute")


ASSERTION_TARGET_CATEGORIES = (
    "missing_alias",
    "missing_exported_key",
    "wrong_canonical_enum_value",
    "missing_project_contract_field",
    "docs_overclaim",
    "unclassified",
)

_PROJECT_CONTRACT_FIELD_TOKENS = (
    "workspace_root",
    "branch_namespace",
    "state_namespace",
    "carry_forward_memory_namespace",
    "project_workspace_root",
    "project_repo_root",
)

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


def _coerce_failure_text(kind: str, message: str, category: str) -> str:
    return f"{kind}\n{category}\n{message}".lower()



COLLECTION_IMPORT_FAILURE_CATEGORY = "collection_import_failure"
_COLLECTION_FAILURE_TOKENS = (
    "error collecting",
    "while importing test module",
    "during collection",
    "pytestcollectionwarning",
)
_COLLECTION_IMPORT_DETAIL_TOKENS = (
    "cannot import name",
    "has no attribute",
    "unexpected keyword argument",
    "importerror",
    "modulenotfounderror",
    "attributeerror",
    "keyerror",
)


def classify_collection_failure(*, kind: str, message: str, category: str = "") -> str:
    normalized_category = str(category or "").strip()
    if normalized_category == COLLECTION_IMPORT_FAILURE_CATEGORY:
        return COLLECTION_IMPORT_FAILURE_CATEGORY
    text = _coerce_failure_text(kind, message, normalized_category)
    if any(token in text for token in _COLLECTION_FAILURE_TOKENS):
        return COLLECTION_IMPORT_FAILURE_CATEGORY
    if (
        any(token in text for token in _COLLECTION_IMPORT_DETAIL_TOKENS)
        and any(token in text for token in ("tests/", "test_", "importing test module", "collection"))
    ):
        return COLLECTION_IMPORT_FAILURE_CATEGORY
    return ""


def is_collection_failure(*, kind: str, message: str, category: str = "") -> bool:
    return bool(classify_collection_failure(kind=kind, message=message, category=category))




def classify_assertion_repair_target(
    *,
    kind: str,
    message: str,
    category: str = "",
    touched_files: Iterable[str] | None = None,
    task_file: str = "",
) -> dict[str, Any]:
    raw_message = str(message or "")
    text = _coerce_failure_text(kind, raw_message, category)
    hinted_files = controller_family_files_touched([*(touched_files or ()), task_file], details=raw_message)

    def _target(surface: str, *, category_name: str, rationale: str, confidence: float, explicit_targets: list[str] | None = None) -> dict[str, Any]:
        target_files = explicit_targets if explicit_targets is not None else _target_files_for_surface(
            surface,
            task_file=task_file,
            touched_files=hinted_files or touched_files,
        )
        return {
            "assertion_target_category": category_name,
            "chosen_repair_target": surface,
            "targeted_patch_surface": surface,
            "target_files": target_files,
            "prefer_minimal_patch": surface != "broad_builder_repair",
            "minimal_patch_selected": surface != "broad_builder_repair",
            "max_files_to_edit": 0 if surface == "manual_stop" else (2 if surface in {"compatibility_alias_only", "import_line_only"} else 3),
            "assertion_target_rationale": rationale,
            "assertion_target_confidence": confidence,
            "narrow_repair_selected": surface in {"compatibility_alias_only", "result_shape_adapter", "manifest_schema_adapter", "controller_contract_surface", "docs_claim_sync"},
            "repair_target_priority": "narrow_first" if surface != "broad_builder_repair" else "broad_fallback",
        }

    if str(category or "").strip() == "docs_proof_claim_drift" or (
        "failed to reach green" in text and any(token in text for token in ("readme", "project state", "product spec", "proof claim", "tasks 090", "tasks 123", "complete"))
    ):
        return _target(
            "docs_claim_sync",
            category_name="docs_overclaim",
            rationale="Assertion evidence points to docs/status overclaim while validation is still red.",
            confidence=0.98,
            explicit_targets=["README.md", "docs/TRADINGBOT_PROJECT_STATE.md", "docs/ORCHESTRATOR_PRODUCT_SPEC.md"],
        )

    if any(field in text for field in _PROJECT_CONTRACT_FIELD_TOKENS) and any(token in text for token in ("keyerror", "missing", "assert isinstance(contract")):
        return _target(
            "compatibility_alias_only",
            category_name="missing_project_contract_field",
            rationale="Assertion evidence points to a missing project contract convenience field or namespace alias.",
            confidence=0.95,
            explicit_targets=["agents/lib/project_registry.py", "agents/run_task.py"],
        )

    if "unexpected keyword argument" in text or "missing `path` or `task_path`" in text or "repair_attempt_budget" in text:
        return _target(
            "compatibility_alias_only",
            category_name="missing_alias",
            rationale="Assertion evidence points to alias drift; repair the smallest compatibility seam before broader rewrites.",
            confidence=0.95,
        )

    if any(token in text for token in ("has no attribute", "cannot import name", "imports missing symbol", "unknown export key", "module 'agents.run_task' has no attribute")):
        explicit = ["agents/run_task.py"] if "run_task" in raw_message else None
        return _target(
            "compatibility_alias_only",
            category_name="missing_exported_key",
            rationale="Assertion evidence points to a missing exported key or symbol on a public/tested seam.",
            confidence=0.94,
            explicit_targets=explicit,
        )

    decision_mismatches = _decision_mismatches(raw_message)
    if decision_mismatches or ("assert" in text and any(token in text for token in ("manual_patch_required", "failed_checks", "failed_merge", "failed_reset", "next_task_may_proceed"))):
        return _target(
            "controller_contract_surface",
            category_name="wrong_canonical_enum_value",
            rationale="Assertion evidence points to canonical enum/status drift; prefer a controller vocabulary fix over a broad rewrite.",
            confidence=0.92,
            explicit_targets=["agents/lib/controller_contract.py", "agents/lib/batch_executor.py", "agents/lib/batch_state.py"],
        )

    return _target(
        "broad_builder_repair",
        category_name="unclassified",
        rationale="No narrow assertion-targeted seam was confidently identified.",
        confidence=0.0,
        explicit_targets=[],
    )

def choose_repair_strategy(
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
    text = _coerce_failure_text(kind, message, category)
    normalized_category = str(category or "").strip()

    targeted = infer_targeted_repair_surface(
        kind=kind,
        message=message,
        category=normalized_category,
        touched_files=touched_files,
        task_file=task_file,
    )
    assertion_target = classify_assertion_repair_target(
        kind=kind,
        message=message,
        category=normalized_category,
        touched_files=touched_files,
        task_file=task_file,
    )
    route = {
        "failure_kind": str(kind or "unknown").strip() or "unknown",
        "failure_category": normalized_category,
        "repair_strategy": "manual_stop",
        "remediation_lane": "operator",
        "next_role": "operator",
        "continue_autonomously": False,
        "stop_after_failure": True,
        "manual_lane_recommended": True,
        "rationale": "Failure is not safely repairable without explicit operator intervention.",
        "route_rationale": "Failure is not safely repairable without explicit operator intervention.",
        "semantic_failure_digest": digest,
        "assertion_target_category": str(assertion_target.get("assertion_target_category") or ""),
        "chosen_repair_target": str(assertion_target.get("chosen_repair_target") or targeted.get("targeted_patch_surface") or ""),
        "assertion_target_confidence": float(assertion_target.get("assertion_target_confidence", 0.0) or 0.0),
        "assertion_target_rationale": str(assertion_target.get("assertion_target_rationale") or ""),
        "narrow_repair_selected": bool(assertion_target.get("narrow_repair_selected", False)),
        "repair_target_priority": str(assertion_target.get("repair_target_priority") or "broad_fallback"),
        **targeted,
    }

    if normalized_category == POLICY_BLOCKED_FAILURE_CATEGORY:
        route["rationale"] = "Policy-blocked failures must remain manual stop signals."
        return route

    collection_category = classify_collection_failure(kind=kind, message=message, category=normalized_category)
    if collection_category:
        if assertion_target.get("assertion_target_category") not in {"", "unclassified"}:
            route.update(**assertion_target)
        route.update(
            failure_category=collection_category,
            repair_strategy="collection_import_contract_repair",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Collection-time import, symbol, and public-surface failures should route to the builder for narrow compatibility repair before broader test retries.",
            route_rationale="Collection-time import, symbol, and public-surface failures should route to the builder for narrow compatibility repair before broader test retries.",
        )
        return route

    if any(token in text for token in ("bootstrap", "venv", "pip install", "missing executable", "no such file or directory", "environment", "setup.py", "pyproject", "toolchain")) or normalized_category == "environment_setup_failure":
        route.update(
            repair_strategy="environment_setup_triage",
            remediation_lane="operator",
            next_role="operator",
            continue_autonomously=False,
            stop_after_failure=True,
            manual_lane_recommended=True,
            rationale="Environment or bootstrap failures should stop conservatively for operator triage.",
            route_rationale="Environment or bootstrap failures should stop conservatively for operator triage.",
        )
        return route

    if normalized_category in {"ci_only_failure", "failed_checks", "failed_merge", "failed_reset"} or any(
        token in text for token in ("required check", "github actions", "ci", "merge-posture", "branch checks", "no checks reported")
    ):
        route.update(
            repair_strategy="ci_verification_recheck",
            remediation_lane="verifier",
            next_role="verifier",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="CI-only and merge-posture failures belong to the verifier lane before the builder retries code changes.",
            route_rationale="CI-only and merge-posture failures belong to the verifier lane before the builder retries code changes.",
        )
        return route

    if normalized_category == "bundle_empty_response":
        route.update(
            repair_strategy="bundle_empty_response_retry",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Zero-file bundle responses should route back to the builder with explicit empty-bundle recovery guidance.",
            route_rationale="Zero-file bundle responses should route back to the builder with explicit empty-bundle recovery guidance.",
        )
        return route

    if normalized_category == "bundle_underfilled_response":
        route.update(
            repair_strategy="missing_deliverable_retry",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Underfilled bundles should route back to the builder with exact missing-deliverable evidence.",
            route_rationale="Underfilled bundles should route back to the builder with exact missing-deliverable evidence.",
        )
        return route

    if normalized_category in {"bundle_markerless_transport", "bundle_malformed_transport", "python_syntax", "imports", "lint", "bundle_transport"} or any(
        token in text for token in ("syntaxerror", "modulenotfounderror", "ruff", "lint", "importerror", "begin_file_bundle")
    ):
        repair_strategy = "bundle_transport_format_retry" if normalized_category in {"bundle_markerless_transport", "bundle_malformed_transport", "bundle_transport"} else "syntax_import_lint_repair"
        rationale = "Markerless/malformed transport failures should route back to the builder with strict transport guidance." if normalized_category in {"bundle_markerless_transport", "bundle_malformed_transport", "bundle_transport"} else "Syntax, import, lint, and transport failures should route back to the builder for targeted repair."
        route.update(
            repair_strategy=repair_strategy,
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale=rationale,
            route_rationale=rationale,
        )
        return route

    if normalized_category in {"tests", "behavioral_regression"} or digest.get("failing_tests"):
        if assertion_target.get("assertion_target_category") not in {"", "unclassified"}:
            route.update(**assertion_target)
        route.update(
            repair_strategy="behavioral_test_repair",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Failing tests and behavioral regressions should route to the builder with exact failing evidence.",
            route_rationale="Failing tests and behavioral regressions should route to the builder with exact failing evidence.",
        )
        return route

    if normalized_category in {"seam_contract_mismatch", "controller_patch_quality", "file_local_semantic_failure"} or bool(digest.get("is_controller_failure")):
        route.update(
            repair_strategy="controller_contract_repair",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Controller-contract and semantic drift failures require targeted builder repair using the semantic digest.",
            route_rationale="Controller-contract and semantic drift failures require targeted builder repair using the semantic digest.",
        )
        return route

    if normalized_category == "docs_proof_claim_drift" or any(token in text for token in ("proof-claim", "proof claim", "docs/", "readme", "documentation claim", "status narrative")):
        if assertion_target.get("assertion_target_category") not in {"", "unclassified"}:
            route.update(**assertion_target)
        route.update(
            repair_strategy="docs_proof_claim_repair",
            remediation_lane="builder",
            next_role="builder",
            continue_autonomously=True,
            stop_after_failure=False,
            manual_lane_recommended=False,
            rationale="Documentation and proof-claim drift should route to the builder with conservative proof-alignment fixes.",
            route_rationale="Documentation and proof-claim drift should route to the builder with conservative proof-alignment fixes.",
        )
        return route

    if assertion_target.get("assertion_target_category") not in {"", "unclassified"}:
        route.update(**assertion_target)
    return route


def format_repair_strategy(route: dict[str, Any] | None) -> str:
    payload = dict(route or {})
    if not payload:
        return ""
    return "\n".join(
        [
            "Repair strategy router:",
            f"- repair_strategy: {payload.get('repair_strategy', '')}",
            f"- remediation_lane: {payload.get('remediation_lane', '')}",
            f"- next_role: {payload.get('next_role', '')}",
            f"- continue_autonomously: {bool(payload.get('continue_autonomously', False))}",
            f"- stop_after_failure: {bool(payload.get('stop_after_failure', False))}",
            f"- targeted_patch_surface: {payload.get('targeted_patch_surface', '')}",
            f"- chosen_repair_target: {payload.get('chosen_repair_target', '')}",
            f"- assertion_target_category: {payload.get('assertion_target_category', '')}",
            f"- target_files: {', '.join(str(item) for item in payload.get('target_files', []))}",
            f"- minimal_patch_selected: {bool(payload.get('minimal_patch_selected', False))}",
            f"- rationale: {payload.get('rationale', '')}",
        ]
    )


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
    route = choose_repair_strategy(
        kind=kind,
        message=message,
        category=category,
        touched_files=touched_files,
        task_file=task_file,
    )
    lines = [
        "Focused controller repair required.",
        "Use the semantic failure digest and explicit repair strategy below in addition to the raw failing output.",
        "Repair the named controller surfaces first; do not rely only on stack traces.",
    ]
    if str(task_file or "").strip():
        lines.insert(1, f"Task file: {task_file}")
    formatted_digest = format_controller_failure_digest(digest)
    if formatted_digest:
        lines.append(formatted_digest)
    formatted_route = format_repair_strategy(route)
    if formatted_route:
        lines.append(formatted_route)
    return {
        "semantic_failure_digest": digest,
        "repair_strategy": route,
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
