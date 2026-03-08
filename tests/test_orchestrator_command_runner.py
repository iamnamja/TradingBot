from __future__ import annotations

import subprocess
from unittest.mock import patch

import pytest

from builder.orchestrator.command_runner import CommandRunner


@pytest.fixture
def command_runner():
    return CommandRunner()


@patch("builder.orchestrator.command_runner.subprocess.run")
def test_execute_success(mock_run, command_runner):
    mock_run.return_value = subprocess.CompletedProcess(
        args="echo Hello World",
        returncode=0,
        stdout="Hello World\n",
        stderr="",
    )

    result = command_runner.execute("echo Hello World")

    assert result["returncode"] == 0
    assert result["stdout"] == "Hello World"
    assert result["stderr"] == ""


@patch("builder.orchestrator.command_runner.subprocess.run")
def test_execute_failure(mock_run, command_runner):
    mock_run.return_value = subprocess.CompletedProcess(
        args="bad-command",
        returncode=1,
        stdout="",
        stderr="command failed",
    )

    result = command_runner.execute("bad-command")

    assert result["returncode"] != 0
    assert result["stdout"] == ""
    assert result["stderr"] == "command failed"


@patch("builder.orchestrator.command_runner.subprocess.run")
def test_execute_timeout(mock_run, command_runner):
    mock_run.side_effect = subprocess.TimeoutExpired(
        cmd='python -c "import time; time.sleep(5)"',
        timeout=0.01,
        output="",
        stderr="Command timed out.",
    )

    result = command_runner.execute('python -c "import time; time.sleep(5)"', timeout=0.01)

    assert result["returncode"] == 124
    assert result["stdout"] == ""
    assert result["stderr"] == "Command timed out."
