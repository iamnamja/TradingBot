from __future__ import annotations

import importlib
import sys
from pathlib import Path



def _load_modules():
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    corpus = importlib.import_module("agents.lib.task_eval_corpus")
    run_task = importlib.import_module("agents.run_task")
    return corpus, run_task



def test_external_safe_eval_manifest_has_canonical_shape() -> None:
    corpus, _ = _load_modules()

    manifest = corpus.external_safe_eval_manifest_snapshot()
    assert manifest["corpus_id"] == "external_safe_v1"
    assert manifest["schema_version"] == 1
    assert manifest["scope"] == "external_safe_one_task_execution_quality"
    assert manifest["item_count"] >= 6
    assert len(manifest["items"]) == manifest["item_count"]
    assert set(manifest["archetypes"]) >= {
        "focused_feature_work",
        "ordinary_bug_fix",
        "targeted_tests",
        "constrained_docs",
    }
    assert set(manifest["validation_profiles"]) >= {
        "tests_only_full_repo",
        "docs_only_full_repo",
        "docs_and_tests_full_repo",
    }



def test_external_safe_eval_items_are_unique_and_contract_valid() -> None:
    corpus, run_task = _load_modules()

    manifest = corpus.external_safe_eval_manifest_snapshot()
    seen: set[str] = set()
    for item in manifest["items"]:
        item_id = item["item_id"]
        assert item_id not in seen
        seen.add(item_id)
        assert item["archetype"] in manifest["archetypes"]
        assert item["validation_profile"] in manifest["validation_profiles"]
        assert item["allowed_execution_lane"] in {"autonomous_safe", "supervised_only", "escalation_required"}
        assert item["autonomy_allowlist_family"] in {"docs_only", "tests_only", "docs_and_tests", "tradingbot_code_only", "tradingbot_code_with_docs_or_tests", ""}
        assert item["required_paths"]

        parsed = run_task.parse_required_files(item["task_text"])
        assert parsed == item["required_paths"]
        valid, _message = run_task.validate_exact_deliverable_contract(item["task_text"])
        assert valid is True



def test_run_task_wrappers_surface_external_safe_eval_manifest() -> None:
    corpus, run_task = _load_modules()

    manifest = run_task.external_safe_eval_manifest_snapshot()
    assert manifest["corpus_id"] == corpus.EXTERNAL_SAFE_EVAL_CORPUS_ID
    assert manifest["item_count"] == len(run_task.list_external_safe_eval_items())

    first = manifest["items"][0]
    fetched = run_task.get_external_safe_eval_item(first["item_id"])
    assert fetched["item_id"] == first["item_id"]
    assert fetched["required_paths"] == first["required_paths"]
    assert run_task.external_safe_eval_archetypes()[first["archetype"]]["description"]
    assert run_task.external_safe_eval_validation_profiles()[first["validation_profile"]]["description"]



def test_external_safe_eval_manifest_only_contains_bounded_safe_paths() -> None:
    corpus, _ = _load_modules()

    manifest = corpus.external_safe_eval_manifest_snapshot()
    for item in manifest["items"]:
        for path in item["required_paths"]:
            assert path == "README.md" or path.startswith("docs/") or path.startswith("tests/")
