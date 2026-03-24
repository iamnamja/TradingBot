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


def _run_command_with_heartbeat(
    cmd: List[str],
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
        cmd,
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


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def run_checks() -> Dict[str, Any] | Tuple[bool, str]:
    heartbeat_seconds = max(5, _int_env("TRADINGBOT_CHECK_HEARTBEAT_SECONDS", 15))
    ruff_timeout_seconds = max(30, _int_env("TRADINGBOT_RUFF_TIMEOUT_SECONDS", 180))
    pytest_timeout_seconds = max(60, _int_env("TRADINGBOT_PYTEST_TIMEOUT_SECONDS", 600))

    lint_ok, lint_output, lint_timed_out = _run_command_with_heartbeat(
        [sys.executable, "-m", "ruff", "check", "."],
        label="ruff check .",
        timeout_seconds=ruff_timeout_seconds,
        heartbeat_seconds=heartbeat_seconds,
    )
    test_ok, test_output, test_timed_out = _run_command_with_heartbeat(
        [sys.executable, "-m", "pytest", "-q"],
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
