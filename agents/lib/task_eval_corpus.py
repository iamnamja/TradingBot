from __future__ import annotations

import copy
from typing import Dict, Mapping, Sequence

EXTERNAL_SAFE_EVAL_CORPUS_ID = "external_safe_v1"
EXTERNAL_SAFE_EVAL_SCHEMA_VERSION = 1


EXTERNAL_SAFE_EVAL_ARCHETYPES: Dict[str, Dict[str, object]] = {
    "focused_feature_work": {
        "description": "Small external-style feature addition or behavior adjustment with explicit file targets.",
        "expected_scope": "single bounded feature slice",
    },
    "ordinary_bug_fix": {
        "description": "Targeted external-style bug fix with a regression-oriented task shape.",
        "expected_scope": "one bounded defect repair",
    },
    "targeted_tests": {
        "description": "Focused assertion or coverage expansion without widening into control-plane work.",
        "expected_scope": "tests-only safe task",
    },
    "constrained_docs": {
        "description": "Ordinary documentation clarification bounded to explicit docs paths.",
        "expected_scope": "docs-only safe task",
    },
}


EXTERNAL_SAFE_EVAL_VALIDATION_PROFILES: Dict[str, Dict[str, object]] = {
    "tests_only_full_repo": {
        "description": "Focused test target first, then standard repo-wide lint and test validation.",
        "focused_validation_kind": "pytest_targeted",
        "full_validation_commands": ["ruff check .", "py -m pytest -q"],
    },
    "docs_only_full_repo": {
        "description": "Constrained docs update followed by normal repo-wide lint and test validation.",
        "focused_validation_kind": "docs_sanity",
        "full_validation_commands": ["ruff check .", "py -m pytest -q"],
    },
    "docs_and_tests_full_repo": {
        "description": "Docs-plus-tests task with targeted pytest first and normal repo-wide validation after.",
        "focused_validation_kind": "pytest_targeted",
        "full_validation_commands": ["ruff check .", "py -m pytest -q"],
    },
}


_CORPUS_ITEM_SPECS: tuple[dict[str, object], ...] = (
    {
        "item_id": "feature_budget_rollup",
        "title": "External-safe feature: budget rollup helper",
        "archetype": "focused_feature_work",
        "validation_profile": "tests_only_full_repo",
        "goal": "Add a small external-style feature helper in a fixture app with a matching focused regression test.",
        "required_paths": (
            "tests/fixtures/external_safe_corpus/budget_app/rollup.py",
            "tests/test_external_safe_budget_rollup.py",
        ),
    },
    {
        "item_id": "bugfix_parser_normalization",
        "title": "External-safe bug fix: parser normalization edge case",
        "archetype": "ordinary_bug_fix",
        "validation_profile": "tests_only_full_repo",
        "goal": "Repair a bounded normalization bug in a fixture parser module and prove it with a regression test.",
        "required_paths": (
            "tests/fixtures/external_safe_corpus/parser_app/normalize.py",
            "tests/test_external_safe_parser_normalization.py",
        ),
    },
    {
        "item_id": "tests_scheduler_guardrail",
        "title": "External-safe tests: scheduler guardrail assertions",
        "archetype": "targeted_tests",
        "validation_profile": "tests_only_full_repo",
        "goal": "Expand a focused assertion surface for an external-style scheduler guardrail without touching control-plane code.",
        "required_paths": (
            "tests/test_external_safe_scheduler_guardrail.py",
        ),
    },
    {
        "item_id": "docs_operator_quickstart",
        "title": "External-safe docs: operator quickstart clarification",
        "archetype": "constrained_docs",
        "validation_profile": "docs_only_full_repo",
        "goal": "Clarify a bounded external-style operator quickstart document without widening into code changes.",
        "required_paths": (
            "docs/external_safe_corpus/operator_quickstart.md",
        ),
    },
    {
        "item_id": "docs_and_tests_api_usage",
        "title": "External-safe docs + tests: API usage example sync",
        "archetype": "constrained_docs",
        "validation_profile": "docs_and_tests_full_repo",
        "goal": "Synchronize a usage-note document with a focused example test for an external-style API slice.",
        "required_paths": (
            "docs/external_safe_corpus/api_usage.md",
            "tests/test_external_safe_api_usage_examples.py",
        ),
    },
    {
        "item_id": "feature_flags_defaults",
        "title": "External-safe feature: feature-flag defaults helper",
        "archetype": "focused_feature_work",
        "validation_profile": "tests_only_full_repo",
        "goal": "Add or adjust a narrow defaults helper in a fixture feature-flags module and prove it with a targeted test.",
        "required_paths": (
            "tests/fixtures/external_safe_corpus/flags_app/defaults.py",
            "tests/test_external_safe_flag_defaults.py",
        ),
    },
)



def _normalize_paths(paths: Sequence[str] | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for raw in paths or ():
        path = str(raw or "").strip().replace("\\", "/")
        if not path or path in seen:
            continue
        out.append(path)
        seen.add(path)
    return out



def _classify_allowed_execution_lane(required_paths: Sequence[str]) -> tuple[str, str, bool, str]:
    required = _normalize_paths(required_paths)
    if not required:
        return ("supervised_only", "", False, "Manifest item has no explicit required paths.")
    docs_or_root = all(path == "README.md" or path.startswith("docs/") for path in required)
    tests_only = all(path.startswith("tests/") for path in required)
    docs_and_tests = all(path == "README.md" or path.startswith("docs/") or path.startswith("tests/") for path in required)
    tradingbot_code_only = all(path.startswith("src/tradingbot/") for path in required)
    tradingbot_code_with_docs_or_tests = any(path.startswith("src/tradingbot/") for path in required) and all(
        path == "README.md" or path.startswith("docs/") or path.startswith("tests/") or path.startswith("src/tradingbot/")
        for path in required
    )
    if docs_or_root:
        return ("autonomous_safe", "docs_only", True, "Docs-only external-safe manifest item remains in the bounded safe lane.")
    if tests_only:
        return ("autonomous_safe", "tests_only", True, "Tests-only external-safe manifest item remains in the bounded safe lane.")
    if docs_and_tests:
        return ("autonomous_safe", "docs_and_tests", True, "Docs-and-tests external-safe manifest item remains in the bounded safe lane.")
    if tradingbot_code_only:
        return ("autonomous_safe", "tradingbot_code_only", True, "Tradingbot-code-only manifest item remains in the bounded safe lane.")
    if tradingbot_code_with_docs_or_tests:
        return (
            "autonomous_safe",
            "tradingbot_code_with_docs_or_tests",
            True,
            "Tradingbot-code-plus-docs/tests manifest item remains in the bounded safe lane.",
        )
    return ("supervised_only", "", False, "Manifest item falls outside the bounded safe allowlist and stays supervised.")



def _build_task_text(*, title: str, goal: str, required_paths: Sequence[str]) -> str:
    bullet_lines = "\n".join(f"- `{path}`" for path in required_paths)
    return (
        f"# {title}\n\n"
        f"## Goal\n{goal}\n\n"
        "## Create or update these exact files\n"
        f"{bullet_lines}\n"
    )



def _build_corpus_item(spec: Mapping[str, object]) -> Dict[str, object]:
    required_paths = _normalize_paths(spec.get("required_paths", ()))
    task_text = _build_task_text(
        title=str(spec.get("title", "") or ""),
        goal=str(spec.get("goal", "") or ""),
        required_paths=required_paths,
    )
    lane, family, allowed, rationale = _classify_allowed_execution_lane(required_paths)
    focused_targets = [path for path in required_paths if path.startswith("tests/")]
    return {
        "item_id": str(spec.get("item_id", "") or ""),
        "title": str(spec.get("title", "") or ""),
        "archetype": str(spec.get("archetype", "") or ""),
        "allowed_execution_lane": lane,
        "autonomy_allowlist_family": family,
        "autonomous_single_task_allowed": allowed,
        "validation_profile": str(spec.get("validation_profile", "") or ""),
        "required_paths": list(required_paths),
        "focused_validation_targets": focused_targets,
        "task_text": task_text,
        "admission_snapshot": {
            "autonomous_single_task_lane": lane,
            "autonomy_allowlist_family": family,
            "autonomous_single_task_rationale": rationale,
        },
    }


_EXTERNAL_SAFE_EVAL_ITEMS: tuple[Dict[str, object], ...] = tuple(_build_corpus_item(spec) for spec in _CORPUS_ITEM_SPECS)
_EXTERNAL_SAFE_EVAL_BY_ID: Dict[str, Dict[str, object]] = {item["item_id"]: item for item in _EXTERNAL_SAFE_EVAL_ITEMS}



def external_safe_eval_archetypes() -> Dict[str, Dict[str, object]]:
    return copy.deepcopy(EXTERNAL_SAFE_EVAL_ARCHETYPES)



def external_safe_eval_validation_profiles() -> Dict[str, Dict[str, object]]:
    return copy.deepcopy(EXTERNAL_SAFE_EVAL_VALIDATION_PROFILES)



def list_external_safe_eval_items() -> list[Dict[str, object]]:
    return copy.deepcopy(list(_EXTERNAL_SAFE_EVAL_ITEMS))



def get_external_safe_eval_item(item_id: str) -> Dict[str, object]:
    key = str(item_id or "").strip()
    if key not in _EXTERNAL_SAFE_EVAL_BY_ID:
        raise KeyError(f"Unknown external-safe eval corpus item: {item_id}")
    return copy.deepcopy(_EXTERNAL_SAFE_EVAL_BY_ID[key])



def external_safe_eval_manifest_snapshot() -> Dict[str, object]:
    items = list_external_safe_eval_items()
    return {
        "corpus_id": EXTERNAL_SAFE_EVAL_CORPUS_ID,
        "schema_version": EXTERNAL_SAFE_EVAL_SCHEMA_VERSION,
        "scope": "external_safe_one_task_execution_quality",
        "description": (
            "Canonical external-safe evaluation manifest for measuring bounded one-task execution quality "
            "before any wider multi-task or self-hosting autonomy claims."
        ),
        "archetypes": external_safe_eval_archetypes(),
        "validation_profiles": external_safe_eval_validation_profiles(),
        "items": items,
        "item_count": len(items),
        "eligible_autonomous_item_ids": [
            item["item_id"]
            for item in items
            if bool(item.get("autonomous_single_task_allowed", False))
        ],
    }
