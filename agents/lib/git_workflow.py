from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List

Runner = Callable[[List[str], bool], object]


@dataclass(frozen=True)
class GitWorkflowResult:
    ok: bool
    step: str
    message: str

    def to_dict(self) -> Dict[str, object]:
        return {
            "ok": self.ok,
            "step": self.step,
            "message": self.message,
        }


def create_pr(runner: Runner, *, title: str, body: str = "") -> GitWorkflowResult:
    body_arg = body if body else title
    try:
        runner(["gh", "pr", "create", "--title", title, "--body", body_arg], True)
    except Exception as exc:
        return GitWorkflowResult(False, "create_pr", f"failed to create PR: {exc}")
    return GitWorkflowResult(True, "create_pr", "PR created")


def wait_for_required_checks(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "checks", "--watch"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "required_checks", f"required checks failed: {exc}")
    return GitWorkflowResult(True, "required_checks", "required checks passed")


def merge_pr(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "merge", "--squash", "--delete-branch"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "merge_pr", f"merge failed: {exc}")
    return GitWorkflowResult(True, "merge_pr", "PR merged")


def reset_main_clean(runner: Runner) -> GitWorkflowResult:
    commands = [
        ["git", "switch", "main"],
        ["git", "fetch", "origin", "main"],
        ["git", "reset", "--hard", "origin/main"],
        ["git", "clean", "-fd"],
    ]
    try:
        for cmd in commands:
            runner(cmd, True)
        runner(["git", "status", "--porcelain"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "reset_main", f"clean main reset failed: {exc}")
    return GitWorkflowResult(True, "reset_main", "clean main reset complete")


def accepted_task_pr_merge_flow(
    runner: Runner,
    *,
    accepted: bool,
    autonomous_merge_enabled: bool,
    pr_title: str,
    pr_body: str = "",
) -> Dict[str, object]:
    result: Dict[str, object] = {
        "accepted": bool(accepted),
        "autonomous_merge_enabled": bool(autonomous_merge_enabled),
        "stopped_honestly": False,
        "stop_reason": "",
        "created_pr": False,
        "required_checks_passed": False,
        "merged": False,
        "main_reset_clean": False,
        "next_task_may_proceed": False,
    }

    if not accepted:
        result["stop_reason"] = "task not accepted; PR flow skipped"
        return result

    if not autonomous_merge_enabled:
        result["stop_reason"] = "autonomous merge disabled by operator control"
        return result

    created = create_pr(runner, title=pr_title, body=pr_body)
    if not created.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = created.message
        return result
    result["created_pr"] = True

    checks = wait_for_required_checks(runner)
    if not checks.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = checks.message
        return result
    result["required_checks_passed"] = True

    merged = merge_pr(runner)
    if not merged.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = merged.message
        return result
    result["merged"] = True

    reset = reset_main_clean(runner)
    if not reset.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = reset.message
        return result
    result["main_reset_clean"] = True
    result["next_task_may_proceed"] = True
    return result


def report_branch_push_ready(branch: str, *, printer=print) -> None:
    printer(f"Pushed branch: {branch}")
    printer("Create a PR on GitHub for this branch (repo rules require PR).")
