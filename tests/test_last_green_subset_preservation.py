from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def _load_run_task_module():
    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.run_task" in sys.modules:
        del sys.modules["agents.run_task"]
    return importlib.import_module("agents.run_task")


def test_last_green_subset_plan_preserves_non_target_files() -> None:
    run_task = _load_run_task_module()

    plan = run_task.build_last_green_subset_preservation_plan(
        applied_files={"good.py": "new-good", "bad.py": "new-bad"},
        repair_route={
            "repair_strategy": "behavioral_test_repair",
            "chosen_repair_target": "compatibility_alias_only",
            "assertion_target_category": "missing_exported_key",
            "target_files": ["bad.py"],
        },
        kind="tests",
        message="AttributeError: module 'x' has no attribute 'y'",
        category="tests",
        touched_files=["good.py", "bad.py"],
        task_file="tasks/134.md",
    )

    assert plan["preserved_subset_paths"] == ["good.py"]
    assert plan["rollback_subset_paths"] == ["bad.py"]
    assert plan["rollback_scope_limited"] is True
    assert plan["last_known_good_subset_paths"] == ["good.py"]


def test_last_green_subset_plan_falls_back_to_all_applied_files_without_overlap() -> None:
    run_task = _load_run_task_module()

    plan = run_task.build_last_green_subset_preservation_plan(
        applied_files={"good.py": "new-good", "bad.py": "new-bad"},
        repair_route={
            "repair_strategy": "behavioral_test_repair",
            "chosen_repair_target": "compatibility_alias_only",
            "target_files": ["agents/run_task.py"],
        },
        kind="tests",
        message="AttributeError: module 'agents.run_task' has no attribute 'x'",
        category="tests",
        touched_files=["good.py", "bad.py"],
        task_file="tasks/134.md",
    )

    assert plan["preserved_subset_paths"] == []
    assert plan["rollback_subset_paths"] == ["good.py", "bad.py"]
    assert plan["rollback_scope_limited"] is False


def test_restore_file_snapshot_subset_only_rolls_back_failing_subset(tmp_path: Path, monkeypatch) -> None:
    run_task = _load_run_task_module()
    monkeypatch.chdir(tmp_path)

    good = tmp_path / "good.py"
    bad = tmp_path / "bad.py"
    good.write_text("old-good\n", encoding="utf-8")
    bad.write_text("old-bad\n", encoding="utf-8")

    snapshot = run_task.snapshot_file_contents(["good.py", "bad.py"])

    good.write_text("new-good\n", encoding="utf-8")
    bad.write_text("new-bad\n", encoding="utf-8")

    restored = run_task.restore_file_snapshot_subset(snapshot, ["bad.py"])

    assert restored == ["bad.py"]
    assert good.read_text(encoding="utf-8") == "new-good\n"
    assert bad.read_text(encoding="utf-8") == "old-bad\n"


def test_write_last_green_subset_artifact_is_stable(tmp_path: Path) -> None:
    run_task = _load_run_task_module()
    artifact_path = tmp_path / "_last_subset_preservation.json"
    plan = {
        "bounded": True,
        "task_file": "tasks/134.md",
        "repair_strategy": "behavioral_test_repair",
        "chosen_repair_target": "compatibility_alias_only",
        "assertion_target_category": "missing_exported_key",
        "applied_subset_paths": ["good.py", "bad.py"],
        "preserved_subset_paths": ["good.py"],
        "last_known_good_subset_paths": ["good.py"],
        "rollback_subset_paths": ["bad.py"],
        "rollback_scope_limited": True,
    }

    run_task.write_last_green_subset_artifact(artifact_path, plan)

    payload = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert payload["bounded"] is True
    assert payload["preserved_subset_paths"] == ["good.py"]
    assert payload["rollback_subset_paths"] == ["bad.py"]
    assert payload["rollback_scope_limited"] is True
