from __future__ import annotations

import subprocess
from typing import List


def run(cmd: List[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        check=check,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def capture(cmd: List[str]) -> str:
    return run(cmd, check=True).stdout.strip()


def ensure_clean_worktree() -> None:
    status = capture(["git", "status", "--porcelain"])
    if status.strip():
        raise SystemExit("Worktree is not clean. Commit/stash changes first.")


def ensure_branch(branch: str) -> None:
    current = capture(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    if current == branch:
        return
    existing = capture(["git", "branch", "--list", branch])
    if existing.strip():
        run(["git", "checkout", branch], check=True)
    else:
        run(["git", "checkout", "-b", branch], check=True)
