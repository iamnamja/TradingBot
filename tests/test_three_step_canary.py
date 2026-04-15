from __future__ import annotations

import json
from pathlib import Path

import pytest

from agents.lib.three_step_canary import run_three_step_canary, validate_three_step_manifest


def _make_tasks(admitted=True):
    return [
        {"id": "A", "follows": None, "admitted": admitted},
        {"id": "B", "follows": "A", "admitted": admitted},
        {"id": "C", "follows": "B", "admitted": admitted},
    ]


def test_validate_manifest_accepts_exact_three_adjacent_and_admitted():
    ok, reason = validate_three_step_manifest(_make_tasks(admitted=True))
    assert ok is True
    assert reason is None


def test_validate_manifest_rejects_if_not_all_admitted():
    tasks = _make_tasks(admitted=True)
    tasks[1]["admitted"] = False
    ok, reason = validate_three_step_manifest(tasks)
    assert ok is False
    assert reason == "all_three_tasks_must_be_explicitly_admitted"


def test_validate_manifest_rejects_if_not_adjacent_A_to_B():
    tasks = _make_tasks(admitted=True)
    tasks[1]["follows"] = "X"
    ok, reason = validate_three_step_manifest(tasks)
    assert ok is False
    assert reason.startswith("strict_adjacency_required_A_to_B")


def test_validate_manifest_rejects_if_not_adjacent_B_to_C():
    tasks = _make_tasks(admitted=True)
    tasks[2]["follows"] = "X"
    ok, reason = validate_three_step_manifest(tasks)
    assert ok is False
    assert reason.startswith("strict_adjacency_required_B_to_C")


def test_runner_persists_durable_chain_ledger(tmp_path: Path):
    artifacts_dir = tmp_path.as_posix()
    tasks = _make_tasks(admitted=True)
    resume_pairs = {
        "A_to_B": {"resumed": False, "checkpoint": None, "resume_mode": "fresh"},
        "B_to_C": {"resumed": True, "checkpoint": "ckpt-2", "resume_mode": "resume"},
    }

    result = run_three_step_canary(
        tasks,
        artifacts_dir,
        supervision_required=True,
        resume_pairs=resume_pairs,
    )
    assert result["ok"] is True
    assert result["outcome"] == "accepted"
    assert result["session_id"]
    ledger_path = Path(result["ledger_path"])
    assert ledger_path.exists()
    # Ledger directory structure: <artifacts_dir>/three_step_canary/<session_id>/chain_ledger.json
    assert ledger_path.parent.parent.name == "three_step_canary"
    assert ledger_path.name == "chain_ledger.json"

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    assert ledger["session_id"] == result["session_id"]
    assert ledger["tasks_order"] == ["A", "B", "C"]
    assert ledger["admitted_all"] is True
    assert ledger["supervision"]["required"] is True
    assert ledger["supervision"]["mode"] == "supervised"
    assert ledger["adjacency"]["A_to_B"]["adjacency_ok"] is True
    assert ledger["adjacency"]["B_to_C"]["adjacency_ok"] is True
    assert ledger["adjacency"]["B_to_C"]["resume"]["resumed"] is True
    assert ledger["adjacency"]["B_to_C"]["resume"]["checkpoint"] == "ckpt-2"
    assert ledger["terminal_outcome"] == "accepted"


def test_runner_rejects_if_supervision_not_required(tmp_path: Path):
    artifacts_dir = tmp_path.as_posix()
    tasks = _make_tasks(admitted=True)
    result = run_three_step_canary(
        tasks,
        artifacts_dir,
        supervision_required=False,
        resume_pairs=None,
    )
    assert result["ok"] is False
    assert result["outcome"] == "rejected"
    assert result["reason"] == "supervision_required"
    # Even on rejection, a durable ledger should be written
    assert Path(result["ledger_path"]).exists()


def test_runner_blocks_on_non_admitted_or_incompatible_adjacency(tmp_path: Path):
    artifacts_dir = tmp_path.as_posix()

    # Case 1: not all admitted
    tasks1 = _make_tasks(admitted=True)
    tasks1[2]["admitted"] = False
    result1 = run_three_step_canary(tasks1, artifacts_dir, supervision_required=True)
    assert result1["ok"] is False
    assert result1["outcome"] == "rejected"
    assert result1["reason"] == "all_three_tasks_must_be_explicitly_admitted"
    assert Path(result1["ledger_path"]).exists()

    # Case 2: wrong adjacency A->B
    tasks2 = _make_tasks(admitted=True)
    tasks2[1]["follows"] = "X"
    result2 = run_three_step_canary(tasks2, artifacts_dir, supervision_required=True)
    assert result2["ok"] is False
    assert result2["outcome"] == "rejected"
    assert result2["reason"] == "strict_adjacency_required_A_to_B"
    assert Path(result2["ledger_path"]).exists()

    # Case 3: wrong adjacency B->C
    tasks3 = _make_tasks(admitted=True)
    tasks3[2]["follows"] = "X"
    result3 = run_three_step_canary(tasks3, artifacts_dir, supervision_required=True)
    assert result3["ok"] is False
    assert result3["outcome"] == "rejected"
    assert result3["reason"] == "strict_adjacency_required_B_to_C"
    assert Path(result3["ledger_path"]).exists()


def test_runner_enforces_exactly_three_tasks(tmp_path: Path):
    artifacts_dir = tmp_path.as_posix()

    # Fewer than 3
    with pytest.raises(ValueError):
        run_three_step_canary(
            [{"id": "A", "follows": None, "admitted": True},
             {"id": "B", "follows": "A", "admitted": True}],
            artifacts_dir,
        )

    # More than 3
    with pytest.raises(ValueError):
        run_three_step_canary(
            [
                {"id": "A", "follows": None, "admitted": True},
                {"id": "B", "follows": "A", "admitted": True},
                {"id": "C", "follows": "B", "admitted": True},
                {"id": "D", "follows": "C", "admitted": True},
            ],
            artifacts_dir,
        )
