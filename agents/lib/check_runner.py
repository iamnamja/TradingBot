from __future__ import annotations

import os
import subprocess
import sys
import time
from typing import Any, Dict, List, Tuple


def _int_env(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        return int(raw)
    except ValueError:
        return default


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


_DEFAULT_CAPTURE_RESULT = capture_result


def _capture_result_overridden() -> bool:
    return capture_result is not _DEFAULT_CAPTURE_RESULT



def _coerce_completed_output(result: object) -> str:
    stdout = getattr(result, "stdout", "") or ""
    stderr = getattr(result, "stderr", "") or ""
    if stderr and stderr not in stdout:
        return f"{stdout}{stderr}".strip()
    return str(stdout).strip()



def _run_command_with_heartbeat(
    exec_cmd: List[str],
    *,
    label: str,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> Tuple[bool, str, bool]:
    """Run a subprocess with periodic heartbeat messages and a hard timeout.

    Returns: (ok, output_text, timed_out)
    """
    print(f"▶ Running {label}", flush=True)
    start = time.monotonic()
    proc = subprocess.Popen(
        exec_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    while True:
        elapsed = time.monotonic() - start
        remaining = max(0.0, float(timeout_seconds) - elapsed)
        if remaining <= 0:
            proc.kill()
            stdout, _ = proc.communicate()
            timeout_msg = (
                f"\n\n[timeout] {label} exceeded {timeout_seconds}s and was terminated."
            )
            return False, (stdout or "").strip() + timeout_msg, True

        try:
            stdout, _ = proc.communicate(timeout=min(float(heartbeat_seconds), remaining))
            break
        except subprocess.TimeoutExpired:
            print(
                f"⏳ Still running {label}... {int(time.monotonic() - start)}s elapsed",
                flush=True,
            )

    output = (stdout or "").strip()
    ok = proc.returncode == 0
    duration = int(time.monotonic() - start)
    status = "ok" if ok else f"exit={proc.returncode}"
    print(f"✔ Finished {label} ({status}, {duration}s)", flush=True)
    return ok, output, False



def _run_check_command(
    display_cmd: List[str],
    *,
    exec_cmd: List[str],
    label: str,
    timeout_seconds: int,
    heartbeat_seconds: int,
) -> Tuple[bool, str, bool]:
    """Preserve the historical capture_result seam for tests/compatibility.

    When capture_result is monkeypatched, use it with the legacy command surface.
    Otherwise, use the heartbeat + timeout execution path with a venv-reliable
    executable command.
    """
    if _capture_result_overridden():
        print(f"▶ Running {label}", flush=True)
        result = capture_result(display_cmd)
        ok = getattr(result, "returncode", 1) == 0
        output = _coerce_completed_output(result)
        status = "ok" if ok else f"exit={getattr(result, 'returncode', 1)}"
        print(f"✔ Finished {label} ({status}, 0s)", flush=True)
        return ok, output, False

    return _run_command_with_heartbeat(
        exec_cmd,
        label=label,
        timeout_seconds=timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )



def run_checks() -> Dict[str, Any] | Tuple[bool, str]:
    heartbeat_seconds = max(5, _int_env("TRADINGBOT_CHECK_HEARTBEAT_SECONDS", 15))
    ruff_timeout_seconds = max(30, _int_env("TRADINGBOT_RUFF_TIMEOUT_SECONDS", 180))
    pytest_timeout_seconds = max(60, _int_env("TRADINGBOT_PYTEST_TIMEOUT_SECONDS", 600))

    lint_ok, lint_output, lint_timed_out = _run_check_command(
        ["ruff", "check", "."],
        exec_cmd=[sys.executable, "-m", "ruff", "check", "."],
        label="ruff check .",
        timeout_seconds=ruff_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )
    test_ok, test_output, test_timed_out = _run_check_command(
        ["pytest", "-q"],
        exec_cmd=[sys.executable, "-m", "pytest", "-q"],
        label="pytest -q",
        timeout_seconds=pytest_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )

    chunks: List[str] = []
    if not lint_ok:
        chunks.append("=== ruff check . ===")
        if lint_output:
            chunks.append(lint_output)
        if lint_timed_out:
            chunks.append(
                f"ruff timed out after {ruff_timeout_seconds}s. "
                "Increase TRADINGBOT_RUFF_TIMEOUT_SECONDS if this is expected."
            )
    if not test_ok:
        chunks.append("=== pytest -q ===")
        if test_output:
            chunks.append(test_output)
        if test_timed_out:
            chunks.append(
                f"pytest timed out after {pytest_timeout_seconds}s. "
                "Increase TRADINGBOT_PYTEST_TIMEOUT_SECONDS if this is expected."
            )

    output_text = "\n\n".join(chunk for chunk in chunks if chunk).strip()
    return {
        "lint_ok": lint_ok,
        "test_ok": test_ok,
        "output_text": output_text,
    }
