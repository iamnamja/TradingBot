from __future__ import annotations

import re
from pathlib import Path
from typing import Callable, Dict, List, Pattern, Sequence, Tuple


def parse_task_contract_directives(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    contract_directive_re: Pattern[str],
) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {
        "",
        "machine-readable contract directives",
        "critical",
        "current runner baseline - must match exactly",
    }
    for section_name, section_lines in iter_markdown_sections(task_text):
        if section_name not in allowed_sections and "contract" not in section_name:
            continue
        for raw_line in section_lines:
            m = contract_directive_re.match(raw_line)
            if not m:
                continue
            key = m.group(1).strip().upper()
            value = m.group(2).strip()
            directives.setdefault(key, []).append(value)
    return directives


def partition_required_paths_for_normal_bundle(
    required_paths: List[str],
    protected_targets: List[dict[str, object]] | List[str] | None = None,
    protected_meta_paths: Tuple[str, ...] | List[str] | None = None,
    **kwargs: object,
) -> Tuple[List[str], List[str]]:
    if protected_meta_paths is None:
        protected_meta_paths = kwargs.get("protected_meta_harness_paths")

    meta_paths = {
        str(p).strip().replace("\\", "/")
        for p in (protected_meta_paths or ())
        if str(p).strip()
    }

    protected_explicit: set[str] = set()
    for target in protected_targets or []:
        if isinstance(target, dict):
            maybe = target.get("path")
            if isinstance(maybe, str) and maybe.strip():
                protected_explicit.add(maybe.strip().replace("\\", "/"))
        elif isinstance(target, str) and target.strip():
            protected_explicit.add(target.strip().replace("\\", "/"))

    normal: List[str] = []
    protected: List[str] = []
    seen_normal: set[str] = set()
    seen_protected: set[str] = set()

    for raw in required_paths or []:
        if not isinstance(raw, str) or not raw.strip():
            continue
        path = raw.strip().replace("\\", "/")
        is_protected = path in protected_explicit or path in meta_paths
        if is_protected:
            if path not in seen_protected:
                protected.append(path)
                seen_protected.add(path)
        elif path not in seen_normal:
            normal.append(path)
            seen_normal.add(path)
    return normal, protected


CANONICAL_ROOT_DOC_FILES = {"README.md"}
CANONICAL_NARRATIVE_DOC_PREFIXES = ("ORCHESTRATOR_", "TRADINGBOT_")


EXACT_DELIVERABLE_SECTION_TITLES = {
    "deliverables",
    "create or update these exact files",
}
REPO_REQUIRED_PATH_PREFIXES = ("agents/", "src/", "tests/", "docs/", "tasks/")
MARKDOWN_HEADING_RE = re.compile(r"^#{1,6}\s+(.+)$")
LIST_ITEM_RE = re.compile(r"^\s*(?:[-*+]\s+|\d+\.\s+)(.+?)\s*$")
BACKTICK_SPAN_RE = re.compile(r"`([^`]+)`")
ABSOLUTE_PATH_RE = re.compile(r"^(?:[A-Za-z]:[\\/]|/)")
URL_PATH_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*://")
BARE_PATH_RE = re.compile(r"^(README\.md|[A-Za-z0-9_.\-/]+)$")


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


def _normalize_exact_deliverable_candidate(raw: str) -> str:
    candidate = str(raw or "").strip().strip('`').strip('"').strip("'")
    candidate = candidate.split("#", 1)[0].strip()
    candidate = candidate.rstrip(",:;.)")
    return candidate.replace("\\", "/")


def _iter_exact_deliverable_lines(task_text: str) -> List[str]:
    lines = task_text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    collected: List[str] = []
    collecting = False
    for line in lines:
        heading = MARKDOWN_HEADING_RE.match(line.strip())
        if heading:
            title = heading.group(1).strip().lower()
            collecting = title in EXACT_DELIVERABLE_SECTION_TITLES
            continue
        if collecting:
            collected.append(line)
    return collected


def _validate_exact_deliverable_path(candidate: str) -> tuple[str | None, str | None]:
    normalized = _normalize_exact_deliverable_candidate(candidate)
    if not normalized:
        return None, None
    if URL_PATH_RE.match(normalized):
        return None, f"`{candidate}` is not a repo-relative file path."
    if ABSOLUTE_PATH_RE.match(normalized):
        return None, f"`{candidate}` is not a repo-relative file path."
    if not BARE_PATH_RE.match(normalized):
        return None, f"`{candidate}` is not a recognized repo-relative file path."
    canonical = canonical_docs_path_for(normalized)
    if any(part == ".." for part in Path(canonical).parts):
        return None, f"`{candidate}` uses path traversal and is not allowed."
    if canonical == "README.md":
        return canonical, None
    if canonical.startswith(REPO_REQUIRED_PATH_PREFIXES):
        return canonical, None
    return None, f"`{candidate}` is not under an allowed repo-relative path prefix."


def parse_required_files_from_task_text(task_text: str) -> List[str]:
    required: List[str] = []
    seen: set[str] = set()
    for raw_line in _iter_exact_deliverable_lines(task_text):
        line = raw_line.strip()
        if not line:
            continue

        m = LIST_ITEM_RE.match(raw_line)
        candidate_line = m.group(1).strip() if m else line

        candidates: List[str] = []
        spans = BACKTICK_SPAN_RE.findall(candidate_line)
        if spans:
            candidates.extend(spans)
        elif candidate_line:
            candidates.append(candidate_line)

        for candidate in candidates:
            canonical, _issue = _validate_exact_deliverable_path(candidate)
            if canonical and canonical not in seen:
                required.append(canonical)
                seen.add(canonical)
    return required


def exact_deliverable_contract_issues(task_text: str) -> List[str]:
    issues: List[str] = []
    seen_issue: set[str] = set()
    for raw_line in _iter_exact_deliverable_lines(task_text):
        line = raw_line.strip()
        if not line:
            continue
        m = LIST_ITEM_RE.match(raw_line)
        candidate_line = m.group(1).strip() if m else line

        candidates: List[str] = []
        spans = BACKTICK_SPAN_RE.findall(candidate_line)
        if spans:
            candidates.extend(spans)
        elif candidate_line:
            candidates.append(candidate_line)

        for candidate in candidates:
            _canonical, issue = _validate_exact_deliverable_path(candidate)
            if issue and issue not in seen_issue:
                issues.append(issue)
                seen_issue.add(issue)
    return issues


def task_requires_material_update(
    task_text: str,
    normalize_newlines: Callable[[str], str] | None = None,
) -> bool:
    text = (normalize_newlines(task_text) if callable(normalize_newlines) else str(task_text or "")).lower()
    phrases = [
        "must create or update",
        "must be created/updated",
        "must be updated",
        "must be materially updated",
        "materially updated in the same bundle",
        "required deliverables were included but not materially updated",
    ]
    return any(phrase in text for phrase in phrases)


def task_allows_unchanged_cli(
    task_text: str,
    normalize_newlines: Callable[[str], str] | None = None,
) -> bool:
    text = (normalize_newlines(task_text) if callable(normalize_newlines) else str(task_text or "")).lower()
    phrases = [
        "not blocked solely because `cli.py` is unchanged",
        "not blocked solely because cli.py is unchanged",
        "including the current compatible `cli.py` in the bundle is acceptable",
        "including the current compatible cli.py in the bundle is acceptable",
        "do not force unnecessary churn in `cli.py`",
        "do not force unnecessary churn in cli.py",
    ]
    return any(phrase in text for phrase in phrases)




def controller_core_required_paths(
    required_paths: Sequence[str] | None,
    *,
    controller_paths: Sequence[str] | None = None,
) -> List[str]:
    try:
        from agents.lib.controller_contract import CONTROLLER_STRICT_MODE_PATHS  # type: ignore
    except Exception:
        CONTROLLER_STRICT_MODE_PATHS = tuple(controller_paths or ())  # type: ignore[assignment]
    strict_paths = normalize_paths(controller_paths or CONTROLLER_STRICT_MODE_PATHS)
    required = normalize_paths(required_paths)
    strict_set = set(strict_paths)
    return [path for path in required if path in strict_set]


def controller_core_task_context(
    required_paths: Sequence[str] | None,
    *,
    controller_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    touched = controller_core_required_paths(required_paths, controller_paths=controller_paths)
    return {
        "touches_controller_core": bool(touched),
        "controller_required_paths": list(touched),
    }


def task_touches_controller_core(
    required_paths: Sequence[str] | None,
    *,
    controller_paths: Sequence[str] | None = None,
) -> bool:
    return bool(controller_core_task_context(required_paths, controller_paths=controller_paths)["touches_controller_core"])


def normalize_paths(paths: Sequence[str] | None) -> List[str]:
    out: List[str] = []
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
) -> dict[str, List[str]]:
    required = set(normalize_paths(required_paths))
    diff = normalize_paths(branch_diff_paths)

    required_present: List[str] = []
    unexpected: List[str] = []
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
) -> List[str]:
    issues: List[str] = []

    required = set(normalize_paths(validated_required_paths))
    head = set(normalize_paths(head_diff_paths))
    worktree = set(normalize_paths(working_tree_paths))

    missing_in_head = sorted(path for path in required if path not in head)
    if missing_in_head:
        issues.append(
            "Required deliverables are not present in committed HEAD diff: "
            + ", ".join(missing_in_head)
        )

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



def multi_agent_task_context(
    required_paths: Sequence[str] | None,
    *,
    controller_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    from agents.lib.multi_agent_contract import ALLOWED_ROLE_HANDOFFS, AGENT_ROLES, SPECIALIST_ROLES

    controller_context = controller_core_task_context(required_paths, controller_paths=controller_paths)
    return {
        **controller_context,
        "multi_agent_enabled": True,
        "sequential_role_execution_only": True,
        "controller_authority_over_next_role": True,
        "roles": list(AGENT_ROLES),
        "specialist_roles": list(SPECIALIST_ROLES),
        "allowed_handoffs": {role: list(targets) for role, targets in ALLOWED_ROLE_HANDOFFS.items()},
        "active_role": "controller",
        "suggested_first_specialist_role": "builder",
    }
