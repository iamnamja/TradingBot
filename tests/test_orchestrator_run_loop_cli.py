from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

from builder.orchestrator import cli
from builder.orchestrator.project_adapter import ProjectAdapter


def test_run_loop_cli_calls_runner_prints_and_logs_decisions(capsys, tmp_path) -> None:
    audit_path = tmp_path / "audit" / "decision.jsonl"
    mock_runner = MagicMock()
    mock_runner.run_loop.return_value = {
        "processed_tasks": [
            {
                "task_name": "alpha",
                "status": "running",
                "outcome": "success",
                "next_action": "continue",
            },
            {
                "task_name": "beta",
                "status": "no_task",
                "outcome": "noop",
                "next_action": "none",
            },
            {
                "task_name": "none",
                "status": "no_task",
                "outcome": "noop",
                "next_action": "none",
            },
        ],
        "final_status": "completed",
        "count": 3,
        "stopped_reason": "all tasks processed",
    }

    config = ProjectAdapter.get_tradingbot_default_config()
    config.audit_path = str(audit_path)

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config", return_value=config), patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ) as mock_runner_cls:
        with patch("sys.argv", ["cli.py", "run-loop", "--max-tasks", "7"]):
            exit_code = cli.main()

    captured = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    mock_runner_cls.assert_called_once()
    mock_runner.run_loop.assert_called_once_with(max_tasks=7)
    assert captured == [
        "[Task 1] alpha — success (continue)",
        "[Task 2] beta — noop (none)",
        "[Task 3] none — noop (none)",
        "Run complete: completed",
        "Tasks processed: 3",
        "Stopped reason: all tasks processed",
    ]

    assert audit_path.exists()
    with audit_path.open("r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]

    assert len(entries) == 1
    assert entries[0]["task_name"] == "alpha"
    assert entries[0]["outcome"] == "success"
    assert entries[0]["iteration"] == 1
    assert isinstance(entries[0]["timestamp"], str)
    assert "T" in entries[0]["timestamp"]


def test_run_loop_cli_defaults_max_tasks_to_100_and_skips_logging_without_audit_path(
    capsys,
) -> None:
    mock_runner = MagicMock()
    mock_runner.run_loop.return_value = {
        "processed_tasks": [
            {
                "task_name": "alpha",
                "status": "running",
                "outcome": "success",
                "next_action": "continue",
            }
        ],
        "final_status": "idle",
        "count": 1,
        "stopped_reason": "no tasks",
    }

    config = ProjectAdapter.get_tradingbot_default_config()
    config.audit_path = None

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config", return_value=config), patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ):
        with patch("sys.argv", ["cli.py", "run-loop"]):
            exit_code = cli.main()

    captured = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    mock_runner.run_loop.assert_called_once_with(max_tasks=100)
    assert captured == [
        "[Task 1] alpha — success (continue)",
        "Run complete: idle",
        "Tasks processed: 1",
        "Stopped reason: no tasks",
    ]


def test_run_loop_cli_creates_audit_parent_directories(tmp_path) -> None:
    audit_path = tmp_path / "nested" / "logs" / "decision.jsonl"
    mock_runner = MagicMock()
    mock_runner.run_loop.return_value = {
        "processed_tasks": [
            {
                "task_name": "alpha",
                "status": "running",
                "outcome": "success",
                "next_action": "continue",
            }
        ],
        "final_status": "completed",
        "count": 1,
        "stopped_reason": "done",
    }

    config = ProjectAdapter.get_tradingbot_default_config()
    config.audit_path = str(audit_path)

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config", return_value=config), patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ):
        with patch("sys.argv", ["cli.py", "run-loop"]):
            exit_code = cli.main()

    assert exit_code == 0
    assert audit_path.exists()
    assert audit_path.parent.exists()
    with audit_path.open("r", encoding="utf-8") as f:
        entries = [json.loads(line) for line in f if line.strip()]
    assert len(entries) == 1
    assert entries[0]["task_name"] == "alpha"
    assert entries[0]["outcome"] == "success"
    assert entries[0]["iteration"] == 1
