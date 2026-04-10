from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[1]



def _bootstrap_repo_root() -> None:
    repo_root = _repo_root()
    root_str = str(repo_root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)



def _load_run_single_task_module():
    _bootstrap_repo_root()
    for name in ["agents.run_single_task", "agents.run_task"]:
        if name in sys.modules:
            del sys.modules[name]
    return importlib.import_module("agents.run_single_task")




def _task_queue_module():
    _bootstrap_repo_root()
    if "agents.lib.task_queue" in sys.modules:
        del sys.modules["agents.lib.task_queue"]
    return importlib.import_module("agents.lib.task_queue")



def test_build_single_task_canary_metrics_aggregates_retry_and_hosted_authority_signals() -> None:
    runner = _load_run_single_task_module()

    entries = [
        {
            "admission": {
                "autonomous_single_task_allowed": True,
                "autonomous_single_task_lane": "autonomous_safe",
                "autonomy_allowlist_family": "tests_only",
                "proof_task_admission_allowed": True,
            },
            "retry": {
                "retry_count_observed": 1,
                "missing_deliverable_retry_observed": True,
                "coupled_compatibility_repair_observed": False,
                "last_green_subset_preserved_observed": True,
            },
            "validation": {
                "execution_invoked": True,
                "no_checks_reported_observed": True,
            },
            "final_decision": "completed",
        },
        {
            "admission": {
                "autonomous_single_task_allowed": True,
                "autonomous_single_task_lane": "autonomous_safe",
                "autonomy_allowlist_family": "tests_only",
                "proof_task_admission_allowed": True,
            },
            "retry": {
                "retry_count_observed": 2,
                "missing_deliverable_retry_observed": False,
                "coupled_compatibility_repair_observed": True,
                "last_green_subset_preserved_observed": False,
            },
            "validation": {
                "execution_invoked": True,
                "no_checks_reported_observed": False,
            },
            "final_decision": "execution_failed",
        },
        {
            "admission": {
                "autonomous_single_task_allowed": False,
                "autonomous_single_task_lane": "supervised_only",
                "autonomy_allowlist_family": "docs_only",
                "proof_task_admission_allowed": True,
            },
            "retry": {
                "retry_count_observed": 0,
                "missing_deliverable_retry_observed": False,
                "coupled_compatibility_repair_observed": False,
                "last_green_subset_preserved_observed": False,
            },
            "validation": {
                "execution_invoked": False,
                "no_checks_reported_observed": False,
            },
            "final_decision": "blocked_supervised_only",
        },
    ]

    metrics = runner.build_single_task_canary_metrics(entries=entries, ledger_path="artifacts/autonomous_single_task/run_ledger.jsonl")

    assert metrics["total_runs"] == 3
    assert metrics["admitted_runs"] == 2
    assert metrics["completed_runs"] == 1
    assert metrics["completion_rate"] == 0.5
    assert metrics["hosted_authority_blocked_runs"] == 1
    assert metrics["hosted_authority_blocking_frequency"] == 0.3333
    assert metrics["retry_metrics"]["runs_with_retry_observed"] == 2
    assert metrics["retry_metrics"]["completed_after_retry_runs"] == 1
    assert metrics["retry_metrics"]["retry_convergence_rate"] == 0.5
    assert metrics["retry_metrics"]["missing_deliverable_retry_runs"] == 1
    assert metrics["retry_metrics"]["coupled_compatibility_repair_runs"] == 1
    assert metrics["retry_metrics"]["last_green_subset_preserved_runs"] == 1
    assert metrics["stop_reason_counts"]["blocked_supervised_only"] == 1
    assert metrics["lane_counts"]["autonomous_safe"] == 2



def test_build_single_task_supervised_handoff_artifact_captures_reason_implicated_files_and_next_action() -> None:
    runner = _load_run_single_task_module()

    artifact = runner.build_single_task_supervised_handoff_artifact(
        entry={
            "task_path": "tasks/141_control_plane_task.md",
            "task_name": "141_control_plane_task.md",
            "ledger_path": "artifacts/autonomous_single_task/run_ledger.jsonl",
            "required_paths": ["agents/run_task.py", "tests/test_run_task_runtime_foundations.py"],
            "completed_at": "2026-04-08T18:30:00Z",
            "admission": {
                "autonomous_single_task_lane": "escalation_required",
                "autonomy_allowlist_family": "",
                "self_hosting_control_plane_task": True,
                "self_hosting_control_plane_required_paths": ["agents/run_task.py"],
                "proof_task_detected": True,
                "proof_task_admission_allowed": False,
            },
            "validation": {
                "execution_invoked": False,
                "returncode": None,
                "no_checks_reported_observed": False,
            },
            "escalation": {
                "required": True,
                "reason": "Task touches self-hosting control-plane or harness surfaces and must be escalated for supervised/manual handling.",
            },
            "final_decision": "escalation_required",
        },
        generated_at="2026-04-08T18:30:00Z",
    )

    assert artifact["handoff_required"] is True
    assert artifact["handoff_kind"] == "escalation_required"
    assert artifact["implicated_paths"] == ["agents/run_task.py"]
    assert "self-hosting control-plane" in artifact["handoff_reason"]
    assert "supervised/manual lane" in artifact["next_supervised_action"]


def test_run_autonomous_single_task_persists_ledger_and_reporting_artifacts(tmp_path: Path) -> None:
    runner = _load_run_single_task_module()
    task_path = tmp_path / "139_safe_tests_only_task.md"
    task_path.write_text(
        "# Safe tests-only task\n\n"
        "## Create or update these exact files\n"
        "## Create or update these exact files\n- `tests/test_single_task_runner.py`\n",
        encoding="utf-8",
    )
    ledger_path = tmp_path / "artifacts" / "run_ledger.jsonl"

    timestamps = iter(["2026-04-08T18:00:00Z", "2026-04-08T18:00:01Z"])

    def fake_now() -> str:
        return next(timestamps)

    def fake_executor(command: list[str]) -> dict[str, object]:
        return {
            "command": list(command),
            "returncode": 0,
            "stdout": "=== Iteration 1/4 ===\n=== Iteration 2/4 ===\nAll checks passed!\n[100%]\nno checks reported on the 'task-139-autonomous-single-task-runner-and-ledger' branch\n",
            "stderr": "",
        }

    result = runner.run_autonomous_single_task(
        task_path.as_posix(),
        ledger_path=ledger_path,
        now=fake_now,
        executor=fake_executor,
    )

    assert result["entry"]["final_decision"] == "completed"
    assert Path(result["ledger_path"]).exists()
    ledger_rows = runner.read_single_task_run_ledger(ledger_path=ledger_path)
    assert len(ledger_rows) == 1
    assert ledger_rows[0]["retry"]["retry_count_observed"] == 1

    canary_metrics_path = Path(result["canary_metrics_path"])
    recovery_report_path = Path(result["recovery_report_path"])
    supervised_handoff_path = Path(result["supervised_handoff_path"])
    assert canary_metrics_path.exists()
    assert recovery_report_path.exists()
    assert supervised_handoff_path.exists()

    metrics = json.loads(canary_metrics_path.read_text(encoding="utf-8"))
    recovery = json.loads(recovery_report_path.read_text(encoding="utf-8"))
    handoff = json.loads(supervised_handoff_path.read_text(encoding="utf-8"))

    assert metrics["total_runs"] == 1
    assert metrics["completed_runs"] == 1
    assert metrics["hosted_authority_blocked_runs"] == 1
    assert recovery["total_runs"] == 1
    assert recovery["handoff_required_count"] == 0
    assert recovery["hosted_authority_blocked_runs"] == 1
    assert handoff["handoff_required"] is False
    assert handoff["handoff_kind"] == "none"



def test_run_autonomous_single_task_reports_escalation_without_execution(tmp_path: Path) -> None:
    runner = _load_run_single_task_module()
    task_path = tmp_path / "141_control_plane_task.md"
    task_path.write_text(
        "# Self-hosting control-plane task\n\n"
        "## Create or update these exact files\n"
        "## Create or update these exact files\n- `agents/run_task.py`\n",
        encoding="utf-8",
    )
    ledger_path = tmp_path / "artifacts" / "run_ledger.jsonl"

    result = runner.run_autonomous_single_task(task_path.as_posix(), ledger_path=ledger_path, now=lambda: "2026-04-08T18:10:00Z")

    assert result["entry"]["final_decision"] == "escalation_required"
    assert result["entry"]["validation"]["execution_invoked"] is False
    metrics = result["canary_metrics"]
    recovery = result["recovery_report"]
    handoff = result["supervised_handoff"]
    assert metrics["stop_reason_counts"]["escalation_required"] == 1
    assert recovery["escalation_required_count"] == 1
    assert recovery["handoff_required_count"] == 1
    assert handoff["handoff_required"] is True
    assert handoff["handoff_kind"] == "escalation_required"
    assert handoff["implicated_paths"] == ["agents/run_task.py"]
    assert "supervised/manual lane" in handoff["next_supervised_action"]



def test_run_scheduler_safe_lane_bridge_runs_single_safe_task_and_writes_policy_artifact(tmp_path: Path) -> None:
    runner = _load_run_single_task_module()
    tq = _task_queue_module()
    queue = [
        tq.TaskQueueItem(task_path="tasks/401.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/402.md", ordinal=2),
    ]
    task_texts = {
        "tasks/401.md": "## Create or update these exact files\n- `tests/test_single_task_runner.py`\n",
        "tasks/402.md": "## Create or update these exact files\n- `agents/run_task.py`\n",
    }

    result = runner.run_scheduler_safe_lane_bridge(
        queue,
        task_text_loader=lambda task_path: task_texts[task_path],
        task_runner=lambda task_path, **_kwargs: {
            "entry": {"final_decision": "completed"},
            "task_path": task_path,
        },
        policy_artifact_path=tmp_path / "scheduler_policy.json",
        now=lambda: "2026-04-09T20:50:00Z",
    )

    artifact_path = Path(result["policy_artifact_path"])
    assert artifact_path.exists()
    artifact = json.loads(artifact_path.read_text(encoding="utf-8"))
    assert result["selection"]["selected_task_path"] == "tasks/401.md"
    assert artifact["executed_autonomous_task"] is True
    assert artifact["supervised_handoff_task_paths"] == ["tasks/402.md"]
    assert artifact["requeue_task_paths"] == []



def test_run_scheduler_safe_lane_bridge_refuses_widening_and_requeues_safe_work(tmp_path: Path) -> None:
    runner = _load_run_single_task_module()
    tq = _task_queue_module()
    queue = [
        tq.TaskQueueItem(task_path="tasks/501.md", ordinal=1),
        tq.TaskQueueItem(task_path="tasks/502.md", ordinal=2),
    ]
    task_texts = {
        "tasks/501.md": "## Create or update these exact files\n- `tests/test_single_task_runner.py`\n",
        "tasks/502.md": "## Create or update these exact files\n- `tests/test_task_queue.py`\n",
    }

    result = runner.run_scheduler_safe_lane_bridge(
        queue,
        task_text_loader=lambda task_path: task_texts[task_path],
        task_runner=lambda *_args, **_kwargs: {"entry": {"final_decision": "completed"}},
        policy_artifact_path=tmp_path / "scheduler_policy.json",
        now=lambda: "2026-04-09T20:55:00Z",
    )

    artifact = json.loads(Path(result["policy_artifact_path"]).read_text(encoding="utf-8"))
    assert result["autonomous_result"] is None
    assert artifact["policy_decision"] == "stop_and_requeue"
    assert sorted(artifact["requeue_task_paths"]) == ["tasks/501.md", "tasks/502.md"]
    assert artifact["executed_autonomous_task"] is False
