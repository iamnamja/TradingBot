from __future__ import annotations

import subprocess
from typing import Any, Dict, List, Tuple


def capture_result(cmd: List[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def run_checks() -> Dict[str, Any] | Tuple[bool, str]:
    lint = capture_result(["ruff", "check", "."])
    test = capture_result(["pytest", "-q"])

    lint_ok = lint.returncode == 0
    test_ok = test.returncode == 0

    chunks: List[str] = []
    if not lint_ok:
        chunks.append("=== ruff check . ===")
        chunks.append((lint.stdout or "").strip())
    if not test_ok:
        chunks.append("=== pytest -q ===")
        chunks.append((test.stdout or "").strip())

    output_text = "\n\n".join(chunk for chunk in chunks if chunk).strip()
    return {
        "lint_ok": lint_ok,
        "test_ok": test_ok,
        "output_text": output_text,
    }
