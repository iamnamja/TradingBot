from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Sequence

AcceptanceDecision = Literal["accepted", "retryable_failure", "manual_patch", "blocked"]
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
                "Required deliverables exist only in working tree (validated but uncommitted): "
                + ", ".join(worktree_only_required)
            )
    unexpected_head = sorted(path for path in head if path not in required)
    if unexpected_head:
        issues.append(
            "Unexpected tracked files remain in committed HEAD diff (outside exact required deliverables): "
            + ", ".join(unexpected_head)
        )
    return issues


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
    retryable = False
    manual_required = False
    if extra_artifacts or any("Unexpected tracked files remain" in issue for issue in issues):
        decision: AcceptanceDecision = "blocked"
    elif manual_patch_required:
        decision = "manual_patch"
        manual_required = True
    elif issues:
        decision = "retryable_failure"
        retryable = True
    else:
        decision = "accepted"
    return {
        "task_file": task_file,
        "acceptance_decision": decision,
        "required_paths": required_paths,
        "head_diff_paths": head_paths,
        "working_tree_paths": working_paths,
        "validation_profile": profile,
        "issues": issues,
        "retryable": retryable,
        "manual_patch_required": manual_required,
        "path_classification": classification,
    }
