from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict

from agents.lib.controller_contract import canonical_merge_posture_truth, merge_posture_decision_for_flow_stage

Runner = Callable[[list[str], bool], object]


@dataclass(frozen=True)
class GitWorkflowResult:
    ok: bool
    step: str
    message: str



def create_pr(runner: Runner, *, title: str, body: str = "") -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "create", "--fill", "--title", title, "--body", body], True)
    except Exception as exc:
        return GitWorkflowResult(False, "create_pr", f"PR creation failed: {exc}")
    return GitWorkflowResult(True, "create_pr", "PR created")



def wait_for_required_checks(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "checks", "--watch"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "wait_for_required_checks", f"required checks failed: {exc}")
    return GitWorkflowResult(True, "wait_for_required_checks", "required checks passed")



def merge_pr(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["gh", "pr", "merge", "--merge", "--auto", "--delete-branch"], True)
    except Exception as exc:
        return GitWorkflowResult(False, "merge_pr", f"PR merge failed: {exc}")
    return GitWorkflowResult(True, "merge_pr", "PR merged")



def reset_main_clean(runner: Runner) -> GitWorkflowResult:
    try:
        runner(["git", "switch", "main"], True)
        runner(["git", "fetch", "origin"], True)
        runner(["git", "reset", "--hard", "origin/main"], True)
        runner(["git", "clean", "-fd"], True)
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
        "post_task_decision": "continue",
        "created_pr": False,
        "required_checks_passed": False,
        "merged": False,
        "main_reset_clean": False,
        "accepted_task_pr_flow_completed": False,
        "merged_to_main": False,
        "clean_main_reset_completed": False,
        "next_task_may_proceed": False,
    }

    if not accepted:
        result["stop_reason"] = "task not accepted; PR flow skipped"
        result["post_task_decision"] = "stop"
        result.update(canonical_merge_posture_truth(result))
        return result

    if not autonomous_merge_enabled:
        result["stop_reason"] = "autonomous merge disabled by operator control"
        result["post_task_decision"] = "stop"
        result.update(canonical_merge_posture_truth(result))
        return result

    created = create_pr(runner, title=pr_title, body=pr_body)
    if not created.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = created.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("merge")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["created_pr"] = True

    checks = wait_for_required_checks(runner)
    if not checks.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = checks.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("checks")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["required_checks_passed"] = True

    merged = merge_pr(runner)
    if not merged.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = merged.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("merge")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["merged"] = True
    result["merged_to_main"] = True

    reset = reset_main_clean(runner)
    if not reset.ok:
        result["stopped_honestly"] = True
        result["stop_reason"] = reset.message
        result["post_task_decision"] = merge_posture_decision_for_flow_stage("reset")
        result.update(canonical_merge_posture_truth(result))
        return result
    result["main_reset_clean"] = True
    result["clean_main_reset_completed"] = True
    result.update(
        canonical_merge_posture_truth(
            required_checks_passed=result["required_checks_passed"],
            merged_to_main=result["merged_to_main"],
            clean_main_reset_completed=result["clean_main_reset_completed"],
        )
    )
    result["next_task_may_proceed"] = True
    return result



def report_branch_push_ready(branch: str, *, printer=print) -> None:
    printer(f"Pushed branch: {branch}")
    printer("Create a PR on GitHub for this branch (repo rules require PR).")
