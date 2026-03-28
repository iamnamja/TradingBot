from __future__ import annotations

from typing import Any, Callable, Dict, List, Pattern, Tuple


def parse_task_contract_directives(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    contract_directive_re: Pattern[str],
) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {"", "machine-readable contract directives", "critical", "current runner baseline — must match exactly"}
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


def _norm_path(path: str) -> str:
    return str(path or "").strip().replace("\\", "/").lower()


def classify_task_family(*, task_text: str, required_paths: List[str]) -> Dict[str, Any]:
    text = str(task_text or "")
    lower_text = text.lower()
    norm_paths = [_norm_path(p) for p in required_paths or []]

    docs_only = bool(norm_paths) and all(
        p.startswith("docs/") or p.endswith(".md") or p.endswith(".rst") or p.endswith(".txt")
        for p in norm_paths
    )

    tests_paths = [p for p in norm_paths if p.startswith("tests/")]
    non_test_paths = [p for p in norm_paths if not p.startswith("tests/")]
    narrow_tests_only = bool(tests_paths) and not non_test_paths

    integration_hint_in_text = ("integration" in lower_text) and (
        "test" in lower_text or "coverage" in lower_text or "e2e" in lower_text
    )
    integration_hint_in_paths = any(
        "integration" in p or "e2e" in p or p.endswith("_integration.py") or p.endswith("integration.py")
        for p in norm_paths
    ) or any("integration" in p or "e2e" in p for p in tests_paths)
    integration_test = bool(integration_hint_in_text or integration_hint_in_paths)

    protected_meta_set = {
        "agents/run_task.py",
        "agents/lib/shell_router.py",
        "agents/lib/bundle_parser.py",
        "agents/lib/protected_file_policy.py",
    }
    protected_meta_harness = any(p in protected_meta_set for p in norm_paths) or "harness policy" in lower_text

    risky_seams = set()
    if docs_only:
        risky_seams.add("docs")
    if narrow_tests_only:
        risky_seams.add("tests")
    if integration_test:
        risky_seams.add("integration")
    if protected_meta_harness:
        risky_seams.add("meta_harness")
    if non_test_paths and tests_paths:
        risky_seams.add("mixed_impl_and_tests")

    split_recommended = ("meta_harness" in risky_seams and "integration" in risky_seams) or len(risky_seams) >= 3
    split_reason = ""
    if split_recommended:
        split_reason = "task mixes multiple risky seam families"

    return {
        "docs_only": docs_only,
        "narrow_tests_only": narrow_tests_only,
        "integration_test": integration_test,
        "protected_meta_harness": protected_meta_harness,
        "split_recommended": split_recommended,
        "split_reason": split_reason,
        "risky_seams": sorted(risky_seams),
    }


def compile_lane_prompt_shape(
    *,
    lane: str,
    task_text: str,
    required_paths: List[str],
    family: Dict[str, Any] | None = None,
) -> str:
    _ = task_text
    _ = required_paths
    _ = family

    normalized = str(lane or "").strip().lower()
    if normalized == "docs-only":
        return (
            "Lane request shape: docs-only.\n"
            "- Keep edits constrained to docs artifacts.\n"
            "- Preserve runtime behavior; avoid python code churn unless explicitly required.\n"
            "- Prefer concise, structured sections and deterministic wording."
        )
    if normalized == "narrow-tests-only":
        return (
            "Lane request shape: narrow tests-only.\n"
            "- Focus on targeted failing tests and minimal supporting implementation.\n"
            "- Avoid cross-module refactors.\n"
            "- Keep assertions deterministic and directly tied to acceptance criteria."
        )
    if normalized == "integration-test":
        return (
            "Lane request shape: integration-test.\n"
            "- Validate end-to-end behavior across seams.\n"
            "- Prefer realistic wiring and stable fixtures over mocks where feasible.\n"
            "- Keep setup deterministic and avoid flaky timing."
        )
    if normalized == "protected-meta-harness":
        return (
            "Lane request shape: protected meta-harness.\n"
            "- Respect harness and protected-file policy constraints exactly.\n"
            "- Minimize surface area and avoid broad rewrites.\n"
            "- Favor smallest safe patch that satisfies required behavior."
        )
    return (
        "Lane request shape: default.\n"
        "- Make minimal, deterministic updates aligned with required deliverables and tests."
    )
