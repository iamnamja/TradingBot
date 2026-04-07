from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Pattern, Sequence, Tuple

PROTECTED_META_TASK_HINTS = ("protected", "meta", "controller core", "controller-core", "strict mode")


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





def project_registry_task_context(
    required_paths: Sequence[str] | None,
) -> dict[str, object]:
    from agents.lib.project_registry import project_registry_snapshot

    required = normalize_paths(required_paths)
    registry_paths = {
        'agents/lib/project_registry.py',
        'agents/lib/project_workspace_adapter.py',
        'tests/test_project_registry.py',
        'tests/test_multi_project_adapters.py',
    }
    touched = [path for path in required if path in registry_paths]
    snapshot = project_registry_snapshot()
    return {
        'touches_project_registry_contract': bool(touched),
        'project_registry_required_paths': list(touched),
        'registered_project_ids': list(snapshot['registered_project_ids']),
        'supported_project_workspace_types': list(snapshot['supported_workspace_types']),
        'project_registry_autonomy_lanes': list(snapshot['autonomy_lanes']),
    }



def project_workspace_task_context(
    required_paths: Sequence[str] | None,
) -> dict[str, object]:
    from agents.lib.project_workspace_adapter import workspace_adapter_snapshot

    required = normalize_paths(required_paths)
    workspace_paths = {
        'agents/lib/project_workspace_adapter.py',
        'tests/test_multi_project_adapters.py',
        'tests/test_project_bootstrap_adapter.py',
    }
    touched = [path for path in required if path in workspace_paths]
    snapshot = workspace_adapter_snapshot()
    return {
        'touches_project_workspace_contract': bool(touched),
        'project_workspace_required_paths': list(touched),
        'python_first_scope_only': bool(snapshot['python_first_scope_only']),
        'supported_workspace_consumers': list(snapshot['supported_consumers']),
    }

def task_admission_context(
    required_paths: Sequence[str] | None,
    *,
    task_file: str = "",
    controller_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    from agents.lib.manifest_planner import build_bounded_decomposition_truth

    required = normalize_paths(required_paths)
    controller_context = controller_core_task_context(required, controller_paths=controller_paths)
    registry_context = project_registry_task_context(required)
    workspace_context = project_workspace_task_context(required)
    task_file_text = str(task_file or "").lower()

    doc_like = [path for path in required if path == "README.md" or path.startswith("docs/")]
    test_like = [path for path in required if path.startswith("tests/")]
    code_like = [path for path in required if path.startswith("agents/") or path.startswith("src/")]
    protected_meta_paths = [
        path
        for path in required
        if path.startswith("agents/lib/protected_")
        or path.startswith("agents/lib/controller_")
        or path == "agents/run_task.py"
    ]
    protected_meta_task = bool(controller_context["touches_controller_core"] or protected_meta_paths or any(hint in task_file_text for hint in PROTECTED_META_TASK_HINTS))
    registry_like = bool(registry_context["touches_project_registry_contract"]) or "project registry" in task_file_text or "per-project contract" in task_file_text
    bootstrap_like = bool(workspace_context["touches_project_workspace_contract"]) or "bootstrap" in task_file_text or "workspace" in task_file_text
    proof_like = (bool(required) and len(doc_like) == len(required)) or "proof" in task_file_text or "sync" in task_file_text
    verifier_only = bool(required) and len(test_like) == len(required)
    mixed_surface_groups = sum(bool(group) for group in (code_like, test_like, doc_like))
    ambiguous_task_shape = not bool(required) or mixed_surface_groups >= 3 or (len(required) >= 4 and doc_like and code_like)
    decomposition = build_bounded_decomposition_truth(required)

    if protected_meta_task:
        lane = "manual_only"
        rationale = "Task touches protected/controller/meta surfaces and must not be admitted to autonomous execution."
        decomposition_status = "manual_only"
        decomposition_required = False
        decomposition_summary = "Manual-only task shape; do not auto-decompose into autonomous work units."
    elif registry_like or bootstrap_like or proof_like:
        lane = "supervised_autonomous"
        rationale = "Task shape remains supervised because project-registry/bootstrap/proof work is broader than ordinary autonomous scope."
        decomposition_status = str(decomposition["decomposition_status"])
        decomposition_required = bool(decomposition["bounded_decomposition_required"])
        decomposition_summary = str(decomposition["decomposition_summary"])
    elif ambiguous_task_shape or bool(decomposition["bounded_decomposition_required"]):
        lane = "supervised_autonomous"
        rationale = "Task shape is larger or more ambiguous than the bounded ordinary-autonomy slice and should stay supervised."
        decomposition_status = str(decomposition["decomposition_status"])
        decomposition_required = bool(decomposition["bounded_decomposition_required"])
        decomposition_summary = str(decomposition["decomposition_summary"])
    else:
        lane = "autonomous_ordinary"
        rationale = "Task shape fits the current bounded ordinary-autonomy slice."
        decomposition_status = str(decomposition["decomposition_status"])
        decomposition_required = bool(decomposition["bounded_decomposition_required"])
        decomposition_summary = str(decomposition["decomposition_summary"])

    return {
        **controller_context,
        **registry_context,
        **workspace_context,
        "task_admission_lane": lane,
        "task_admission_rationale": rationale,
        "protected_or_meta_task": protected_meta_task,
        "protected_or_meta_required_paths": list(protected_meta_paths),
        "ambiguous_task_shape": ambiguous_task_shape,
        "ordinary_task_candidate": bool(required) and not protected_meta_task and not bootstrap_like and not proof_like,
        "bounded_decomposition_required": decomposition_required,
        "decomposition_status": decomposition_status,
        "decomposition_unit_count": int(decomposition["decomposition_unit_count"]),
        "decomposition_units": list(decomposition["decomposition_units"]),
        "decomposition_summary": decomposition_summary,
        "verifier_only_task_shape": verifier_only,
        "proof_like_task_shape": proof_like,
        "bootstrap_like_task_shape": bootstrap_like,
        "project_registry_like_task_shape": registry_like,
    }


def task_family_task_context(
    required_paths: Sequence[str] | None,
    *,
    task_file: str = "",
    controller_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    required = normalize_paths(required_paths)
    admission_context = task_admission_context(required, task_file=task_file, controller_paths=controller_paths)
    bootstrap_like = bool(admission_context["bootstrap_like_task_shape"])
    proof_like = bool(admission_context["proof_like_task_shape"])
    verifier_only = bool(admission_context["verifier_only_task_shape"])

    if bool(admission_context["touches_controller_core"]):
        family = "strict_manual_controller_core"
        suggested_role = "manual_patch"
        lane = "constrained_manual"
        strict_required = True
        rationale = "Task touches controller-core surfaces and must remain constrained/manual."
    elif bool(admission_context["protected_or_meta_task"]):
        family = "strict_manual_controller_core"
        suggested_role = "manual_patch"
        lane = "constrained_manual"
        strict_required = True
        rationale = "Task admission gate classified this shape as protected/meta and manual-only."
    elif bootstrap_like:
        family = "bootstrap_setup"
        suggested_role = "builder"
        lane = "bootstrap_setup"
        strict_required = False
        rationale = "Task touches project workspace/bootstrap surfaces."
    elif verifier_only:
        family = "verifier_first"
        suggested_role = "verifier"
        lane = "verifier"
        strict_required = False
        rationale = "Task touches verification/test surfaces only."
    elif proof_like:
        family = "proof_docs"
        suggested_role = "builder"
        lane = "proof_docs"
        strict_required = True
        rationale = "Task is documentation/proof shaping work and should stay under proof guardrails."
    else:
        family = "builder_first"
        suggested_role = "builder"
        lane = "builder"
        strict_required = False
        rationale = "Task defaults to builder-first routing."

    return {
        **admission_context,
        "task_family": family,
        "task_family_rationale": rationale,
        "suggested_first_specialist_role": suggested_role,
        "suggested_initial_lane": lane,
        "strict_mode_required": strict_required,
        "proof_docs_task": family == "proof_docs",
        "bootstrap_setup_task": family == "bootstrap_setup",
        "verifier_first_task": family == "verifier_first",
        "builder_first_task": family == "builder_first",
    }


def multi_agent_task_context(
    required_paths: Sequence[str] | None,
    *,
    controller_paths: Sequence[str] | None = None,
) -> dict[str, object]:
    from agents.lib.multi_agent_contract import ALLOWED_ROLE_HANDOFFS, AGENT_ROLES, SPECIALIST_ROLES

    family_context = task_family_task_context(required_paths, task_file="", controller_paths=controller_paths)
    return {
        **family_context,
        "multi_agent_enabled": True,
        "sequential_role_execution_only": True,
        "controller_authority_over_next_role": True,
        "roles": list(AGENT_ROLES),
        "specialist_roles": list(SPECIALIST_ROLES),
        "allowed_handoffs": {role: list(targets) for role, targets in ALLOWED_ROLE_HANDOFFS.items()},
        "active_role": "controller",
        "suggested_first_specialist_role": "builder",
    }



def _normalize_claim_lines(text: str) -> list[str]:
    return [line.strip().lower().replace('*', '') for line in str(text or '').replace("\r\n", "\n").replace("\r", "\n").split("\n") if line.strip()]


def _claim_line_is_guarded(line: str, phrase: str) -> bool:
    idx = line.find(phrase)
    if idx < 0:
        return False
    prefix = line[:idx]
    return "does not" in prefix or "do not" in prefix or "not " in prefix or "without" in prefix


def validate_proof_sync_contract(
    *,
    run_task_exports: Sequence[str] | None = None,
    multi_agent_loop_exports: Sequence[str] | None = None,
    compatibility_result: Mapping[str, Any] | None = None,
    canonical_result: Mapping[str, Any] | None = None,
    manifest_examples: Sequence[Mapping[str, Any]] | None = None,
    role_snapshot: Mapping[str, Any] | None = None,
    boundary_snapshot: Mapping[str, Any] | None = None,
    claim_texts: Sequence[str] | None = None,
) -> dict[str, object]:
    from agents.lib.controller_contract import proof_sync_contract_snapshot

    spec = proof_sync_contract_snapshot()
    expected_run = {str(x) for x in spec["run_task_exports"]}
    expected_loop = {str(x) for x in spec["multi_agent_loop_exports"]}
    compat_fields = {str(x) for x in spec["compatibility_result_fields"]}
    canonical_fields = {str(x) for x in spec["canonical_result_fields"]}
    allowed_manifest = {str(x) for x in spec["allowed_manifest_entry_keys"]}
    required_boundary = {str(x) for x in spec["required_boundary_keys"]}
    required_role = {str(x) for x in spec["required_role_snapshot_keys"]}
    forbidden_phrases = [str(x) for x in spec["claim_forbidden_phrases"]]

    run_exports = {str(x) for x in (run_task_exports or ())}
    loop_exports = {str(x) for x in (multi_agent_loop_exports or ())}
    compat_present = set((compatibility_result or {}).keys())
    canonical_present = set((canonical_result or {}).keys())
    boundary_present = set((boundary_snapshot or {}).keys())
    role_present = set((role_snapshot or {}).keys())

    manifest_issues: list[str] = []
    for index, entry in enumerate(manifest_examples or []):
        keys = {str(k) for k in entry.keys()}
        unknown = sorted(keys - allowed_manifest)
        if unknown:
            manifest_issues.append(f"manifest entry {index} uses unsupported keys: {', '.join(unknown)}")
        if not ({'path','task_path'} & keys):
            manifest_issues.append(f"manifest entry {index} is missing path/task_path")

    claim_issues: list[str] = []
    for text_block in claim_texts or ():
        previous_line = ""
        negated_claim_section = False
        for line in _normalize_claim_lines(text_block):
            if "does not claim" in line or "does not honestly claim" in line or "it does not claim" in line:
                negated_claim_section = True
                previous_line = line
                continue
            if negated_claim_section and not line.startswith('-'):
                negated_claim_section = False
            guarded_by_context = negated_claim_section or ("does not claim" in previous_line or "does not honestly claim" in previous_line or "it does not claim" in previous_line)
            for phrase in forbidden_phrases:
                if phrase in line and not guarded_by_context and not _claim_line_is_guarded(line, phrase):
                    claim_issues.append(f"unguarded claim phrase: {phrase}")
            previous_line = line

    missing_run = sorted(expected_run - run_exports)
    missing_loop = sorted(expected_loop - loop_exports)
    missing_compat = sorted(compat_fields - compat_present)
    missing_canonical = sorted(canonical_fields - canonical_present)
    missing_boundary = sorted(required_boundary - boundary_present)
    missing_role = sorted(required_role - role_present)

    issues = [
        *[f"missing run_task export: {x}" for x in missing_run],
        *[f"missing multi_agent_loop export: {x}" for x in missing_loop],
        *[f"missing compatibility result field: {x}" for x in missing_compat],
        *[f"missing canonical result field: {x}" for x in missing_canonical],
        *[f"missing boundary snapshot key: {x}" for x in missing_boundary],
        *[f"missing role snapshot key: {x}" for x in missing_role],
        *manifest_issues,
        *claim_issues,
    ]

    return {
        "ok": not issues,
        "issues": issues,
        "missing_run_task_exports": missing_run,
        "missing_multi_agent_loop_exports": missing_loop,
        "missing_compatibility_result_fields": missing_compat,
        "missing_canonical_result_fields": missing_canonical,
        "missing_boundary_snapshot_keys": missing_boundary,
        "missing_role_snapshot_keys": missing_role,
        "manifest_issues": manifest_issues,
        "claim_guard_issues": claim_issues,
    }


def project_scoped_runtime_task_context(
    required_paths: Sequence[str] | None,
    *,
    project_contract: Mapping[str, object] | None = None,
) -> dict[str, object]:
    from agents.lib.project_registry import project_scope_identity

    required = normalize_paths(required_paths)
    identity = project_scope_identity(project_contract)
    return {
        'touches_project_scoped_runtime': bool(required),
        'project_id': str(identity['project_id']),
        'project_identity_ambiguous': bool(identity['project_identity_ambiguous']),
        'project_state_namespace': str(identity['project_state_namespace']),
        'project_checkpoint_namespace': str(identity['project_checkpoint_namespace']),
        'project_branch_namespace': str(identity['project_branch_namespace']),
    }



def dependency_decomposition_task_context(
    required_paths: Sequence[str] | None,
    *,
    decomposition_safe: bool = False,
    max_paths_per_unit: int = 3,
) -> dict[str, object]:
    from agents.lib.manifest_planner import build_manifest_entry_decomposition_truth

    truth = build_manifest_entry_decomposition_truth(
        {
            "required_paths": list(required_paths or ()),
            "decomposition_safe": decomposition_safe,
            "decomposition_max_unit_size": max_paths_per_unit,
        }
    )
    return {
        "decomposition_status": str(truth.get("decomposition_status", "not_required")),
        "bounded_decomposition_required": bool(truth.get("bounded_decomposition_required", False)),
        "decomposition_unit_count": int(truth.get("decomposition_unit_count", 0) or 0),
        "decomposition_summary": str(truth.get("decomposition_summary", "") or ""),
    }
