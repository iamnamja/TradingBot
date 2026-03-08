from __future__ import annotations

import subprocess
from typing import Any


class CommandRunner:
    def execute(self, command: str, timeout: float | None = None) -> dict[str, Any]:
        try:
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            stdout = (result.stdout or "").strip()
            stderr = result.stderr or ""
            return {
                "returncode": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout if isinstance(exc.stdout, str) else ""
            stderr = exc.stderr if isinstance(exc.stderr, str) else ""
            return {
                "returncode": 124,
                "stdout": stdout.strip(),
                "stderr": stderr.strip() or "Command timed out.",
            }
