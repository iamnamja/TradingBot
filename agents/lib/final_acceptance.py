from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

from agents.lib.controller_contract import AcceptanceDecision, coerce_acceptance_decision
from agents.lib.controller_repair import build_controller_repair_context

AcceptanceFailureClass = Literal[
    "missing_required_in_head",
    "required_only_in_worktree",
    "unexpected_tracked_artifact",
    "merge_ready_validation_failed",
]
CANONICAL_ROOT_DOC_FILES = {"README.md"}
CANONICAL_NARRATIVE_DOC_PREFIXES = ("ORCHESTRATOR_", "TRADINGBOT_")


def canonical_docs_path_for(path: str) -> str:
    normalized = str(path or "").strip().replace("\\", "/")
    if not normalized.endswith(".md"):
        return normalized
    if "/" in normalized:
        return normalized
    if normalized in CANONICAL_ROOT_DOC_FILES:
        return normalized
    filename = Path(normalized).name
    if filename.startswith(CANONICAL_NARRATIVE_DOC_PREFIXES):
        return f"docs/{filename}"
    return normalized


def normalize_paths(paths: Sequence[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in paths or ():
        path = str(raw or "").strip().replace("\\", "/")
        if not path:
            continue
        canonical = canonical_docs_path_for(path)
        if canonical not in seen:
            out.append(canonical)
            seen.add(canonical)
    return out


def classify_branch_diff_paths(
    branch_diff_paths: Sequence[str] | None,
    required_paths: Sequence[str] | None,
) -> dict[str, list[str]]:
    required = set(normalize_paths(required_paths))
    diff = normalize_paths(branch_diff_paths)
    required_present: list[str] = []
    unexpected: list[str] = []
    for path in diff:
        if path in required:
            required_present.append(path)
        else:
            unexpected.append(path)
    missing_required = sorted(path for path in required if path not in required_present)
    return {
        "required_present": required_present,
        "missing_required": missing_required,
        "unexpected": unexpected,
    }


def committed_state_parity_issues(
    *,
    validated_required_paths: Sequence[str] | None,
    head_diff_paths: Sequence[str] | None,
    working_tree_paths: Sequence[str] | None,
    strict_required_worktree_only: bool = True,
) -> list[str]:
    issues: list[str] = []
    required = set(normalize_paths(validated_required_paths))
    head = set(normalize_paths(head_diff_paths))
    worktree = set(normalize_paths(working_tree_paths))
    missing_in_head = sorted(path for path in required if path not in head)
    if missing_in_head:
        issues.append("Required deliverables are not present in committed HEAD diff: " + ", ".join(missing_in_head))
    if strict_required_worktree_only:
        worktree_only_required = sorted(path for path in required if path in worktree and path not in head)
        if worktree_only_required:
            issues.append(
                "Required deliverables exist only in working tree (validated but uncommitted): " + ", ".join(worktree_only_required)
            )
    unexpected_head = sorted(path for path in head if path not in required)
    if unexpected_head:
        issues.append(
            "Unexpected tracked files remain in committed HEAD diff (outside exact required deliverables): " + ", ".join(unexpected_head)
        )
    return issues


def classify_final_acceptance_failure(report: dict[str, Any]) -> dict[str, object]:
    issues = [str(issue).strip() for issue in report.get("issues", []) or [] if str(issue).strip()]
    classification = report.get("path_classification", {}) or {}
    missing_required = [str(p) for p in classification.get("missing_required", []) or []]
    unexpected = [str(p) for p in classification.get("unexpected", []) or []]
    working_tree_paths = set(normalize_paths(report.get("working_tree_paths", []) or []))
    required_paths = set(normalize_paths(report.get("required_paths", []) or []))
    head_paths = set(normalize_paths(report.get("head_diff_paths", []) or []))
    worktree_only_required = sorted(p for p in required_paths if p in working_tree_paths and p not in head_paths)

    if any("Authoritative validation profile failed" in issue for issue in issues):
        failure_class = "merge_ready_validation_failed"
        retryable = True
        stop_reason: AcceptanceDecision = "retryable_failure"
    elif missing_required:
        failure_class = "missing_required_in_head"
        retryable = True
        stop_reason = "retryable_failure"
    elif worktree_only_required:
        failure_class = "required_only_in_worktree"
        retryable = True
        stop_reason = "retryable_failure"
    elif unexpected:
        failure_class = "unexpected_tracked_artifact"
        retryable = all(p.startswith("artifacts/") for p in unexpected)
        stop_reason = "blocked"
    else:
        decision = coerce_acceptance_decision(report.get("acceptance_decision"), default="manual_patch")
        failure_class = "merge_ready_validation_failed"
        retryable = decision == "retryable_failure"
        stop_reason = decision if decision in {"blocked", "manual_patch", "retryable_failure"} else "manual_patch"

    return {
        "failure_class": failure_class,
        "retryable": retryable,
        "stop_reason": stop_reason,
        "missing_required": missing_required,
        "required_only_in_worktree": worktree_only_required,
        "unexpected_tracked": unexpected,
        "issues": issues,
    }


def build_acceptance_self_heal_context(report: dict[str, Any]) -> dict[str, object]:
    classification = classify_final_acceptance_failure(report)
    failure_class = str(classification["failure_class"])
    lines = [
        "Focused final-acceptance repair required.",
        f"Acceptance failure class: {failure_class}",
        f"Task file: {report.get('task_file', '')}",
        "Repair only the files and acceptance gap named below. Do not broad-rerun unrelated changes.",
        "Do not rerun raw task execution for this attempt. Repair the current result only, then rerun validation and final acceptance.",
    ]
    if classification["missing_required"]:
        lines.append("Required files missing from committed HEAD diff:")
        lines.extend(f"- {p}" for p in classification["missing_required"])
    if classification["required_only_in_worktree"]:
        lines.append("Required files only present in working tree:")
        lines.extend(f"- {p}" for p in classification["required_only_in_worktree"])
    if classification["unexpected_tracked"]:
        lines.append("Unexpected tracked files to remove from committed diff:")
        lines.extend(f"- {p}" for p in classification["unexpected_tracked"])
    semantic_context: dict[str, Any] = {}
    if failure_class == "merge_ready_validation_failed":
        details = str(((report.get("validation_profile", {}) or {}).get("details", ""))).strip()
        lines.append("Authoritative merge-ready validation failed after nominal green pass.")
        if details:
            semantic_context = build_controller_repair_context(
                kind="final_acceptance",
                message=details,
                category=str(report.get("acceptance_decision", "")),
                touched_files=[
                    *normalize_paths(report.get("required_paths", []) or []),
                    *normalize_paths(report.get("head_diff_paths", []) or []),
                    *normalize_paths(report.get("working_tree_paths", []) or []),
                ],
                task_file=str(report.get("task_file", "")),
            )
            lines.append("Validation details:")
            lines.append(details)
            repair_prompt = str(semantic_context.get("repair_prompt", "")).strip()
            if repair_prompt:
                lines.append("Semantic controller repair context:")
                lines.append(repair_prompt)
    return {
        **classification,
        **({"semantic_failure_digest": semantic_context.get("semantic_failure_digest", {})} if semantic_context else {}),
        "repair_scope": "repair_only",
        "reexecute_task": False,
        "repair_prompt": "\n".join(lines),
    }


def build_final_acceptance_report(
    *,
    task_file: str,
    validated_required_paths: Sequence[str] | None,
    head_diff_paths: Sequence[str] | None,
    working_tree_paths: Sequence[str] | None,
    validation_profile: dict[str, Any] | None,
    unexpected_tracked_artifact_findings: Sequence[str] | None = None,
    manual_patch_required: bool = False,
) -> dict[str, object]:
    required_paths = normalize_paths(validated_required_paths)
    head_paths = normalize_paths(head_diff_paths)
    working_paths = normalize_paths(working_tree_paths)
    profile = {
        "passed": bool((validation_profile or {}).get("passed", False)),
        "details": str((validation_profile or {}).get("details", "")),
    }
    classification = classify_branch_diff_paths(head_paths, required_paths)
    issues = committed_state_parity_issues(
        validated_required_paths=required_paths,
        head_diff_paths=head_paths,
        working_tree_paths=working_paths,
    )
    details = profile["details"].strip()
    if not profile["passed"]:
        issues.insert(0, "Authoritative validation profile failed." + (f" Details: {details}" if details else ""))
    extra_artifacts = [str(item).strip() for item in unexpected_tracked_artifact_findings or () if str(item).strip()]
    for finding in extra_artifacts:
        if finding not in issues:
            issues.append(finding)
    if manual_patch_required:
        decision: AcceptanceDecision = "manual_patch"
    else:
        probe = classify_final_acceptance_failure({
            "issues": issues,
            "path_classification": classification,
            "required_paths": required_paths,
            "head_diff_paths": head_paths,
            "working_tree_paths": working_paths,
            "validation_profile": profile,
            "acceptance_decision": "retryable_failure" if issues else "accepted",
        })
        if not issues:
            decision = "accepted"
        elif str(probe["stop_reason"]) == "blocked":
            decision = "blocked"
        elif str(probe["stop_reason"]) == "retryable_failure":
            decision = "retryable_failure"
        else:
            decision = "manual_patch"
    context = build_acceptance_self_heal_context({
        "task_file": task_file,
        "issues": issues,
        "path_classification": classification,
        "required_paths": required_paths,
        "head_diff_paths": head_paths,
        "working_tree_paths": working_paths,
        "validation_profile": profile,
        "acceptance_decision": decision,
    })
    return {
        "task_file": task_file,
        "acceptance_decision": decision,
        "required_paths": required_paths,
        "head_diff_paths": head_paths,
        "working_tree_paths": working_paths,
        "validation_profile": profile,
        "issues": issues,
        "retryable": bool(context.get("retryable", False)),
        "manual_patch_required": manual_patch_required or decision == "manual_patch",
        "path_classification": classification,
        "self_heal_context": context,
    }


def run_final_acceptance_review(
    *,
    task_file: str,
    validated_required_paths: Sequence[str] | None,
    head_diff_paths: Sequence[str] | None,
    working_tree_paths: Sequence[str] | None,
    validation_profile: dict[str, Any] | None,
    unexpected_tracked_artifact_findings: Sequence[str] | None = None,
    manual_patch_required: bool = False,
) -> dict[str, object]:
    return build_final_acceptance_report(
        task_file=task_file,
        validated_required_paths=validated_required_paths,
        head_diff_paths=head_diff_paths,
        working_tree_paths=working_tree_paths,
        validation_profile=validation_profile,
        unexpected_tracked_artifact_findings=unexpected_tracked_artifact_findings,
        manual_patch_required=manual_patch_required,
    )


def build_final_acceptance_failure_feedback(report: dict[str, Any]) -> str:
    issues = [str(issue).strip() for issue in report.get("issues", []) or [] if str(issue).strip()]
    decision = str(report.get("acceptance_decision", "retryable_failure"))
    lines = [
        "Final acceptance review rejected the current result.",
        f"Acceptance decision: {decision}",
        "Reconcile the exact task contract against the committed/staged diff and final validation before claiming success.",
    ]
    try:
        context = build_acceptance_self_heal_context(report)
    except Exception:
        context = {}
    repair_prompt = str(context.get("repair_prompt", "")).strip()
    if repair_prompt:
        lines.append("Focused self-heal guidance:")
        lines.append(repair_prompt)
    elif issues:
        lines.append("Issues:")
        lines.extend(f"- {issue}" for issue in issues)
    return "\n".join(lines)


def report_final_acceptance_failure(
    report: dict[str, Any],
    *,
    printer: callable = print,
) -> None:
    printer("❌ Final acceptance review failed:")
    issues = [str(issue).strip() for issue in report.get("issues", []) or [] if str(issue).strip()]
    if issues:
        for issue in issues:
            printer(f"- {issue}")
    else:
        printer(f"- acceptance_decision={report.get('acceptance_decision', 'retryable_failure')}")
