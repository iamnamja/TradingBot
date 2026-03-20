from __future__ import annotations

from unittest.mock import MagicMock, patch

import src.builder.orchestrator.cli as cli


def test_run_loop_cli_calls_runner_and_prints_iteration_and_summary(capsys) -> None:
    mock_runner = MagicMock()
    mock_runner.run_loop.return_value = {
        "processed_tasks": [
            {
                "task_name": "alpha",
                "outcome": "success",
                "next_action": "continue",
            },
            {
                "task_name": "beta",
                "outcome": "blocked",
                "next_action": "stop",
            },
        ],
        "final_status": "completed",
        "count": 2,
        "stopped_reason": "all tasks processed",
    }

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config") as mock_config, patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ) as mock_runner_cls:
        mock_config.return_value = MagicMock(tasks_directory="tasks/")
        with patch("sys.argv", ["cli.py", "run-loop", "--max-tasks", "7"]):
            exit_code = cli.main()

    captured = capsys.readouterr().out.splitlines()

    assert exit_code == 0
    mock_runner_cls.assert_called_once()
    mock_runner.run_loop.assert_called_once_with(max_tasks=7)
    assert captured == [
        "[Task 1] alpha — success (continue)",
        "[Task 2] beta — blocked (stop)",
        "Run complete: completed",
        "Tasks processed: 2",
        "Stopped reason: all tasks processed",
    ]


def test_run_loop_cli_defaults_max_tasks_to_100() -> None:
    mock_runner = MagicMock()
    mock_runner.run_loop.return_value = {
        "processed_tasks": [],
        "final_status": "idle",
        "count": 0,
        "stopped_reason": "no tasks",
    }

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config") as mock_config, patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ):
        mock_config.return_value = MagicMock(tasks_directory="tasks/")
        with patch("sys.argv", ["cli.py", "run-loop"]):
            cli.main()

    mock_runner.run_loop.assert_called_once_with(max_tasks=100)


def test_existing_cli_modes_still_parse_and_dispatch() -> None:
    mock_runner = MagicMock()
    mock_runner.simulate_backlog.return_value = {
        "processed_tasks": 3,
        "stopped_reason": "done",
        "final_status": "completed",
    }
    mock_runner.run_next_task.return_value = {
        "task_name": "omega",
        "status": "running",
        "message": "ok",
        "outcome": "noop",
    }

    with patch.object(cli.ProjectAdapter, "get_tradingbot_default_config") as mock_config, patch.object(
        cli, "OrchestratorRunner", return_value=mock_runner
    ):
        mock_config.return_value = MagicMock(tasks_directory="tasks/")

        with patch("sys.argv", ["cli.py", "--simulate"]):
            assert cli.main() == 0

        with patch("sys.argv", ["cli.py", "--dry-run"]):
            assert cli.main() == 0

    mock_runner.simulate_backlog.assert_called_once()
    mock_runner.run_next_task.assert_called_once_with(dry_run=True)
