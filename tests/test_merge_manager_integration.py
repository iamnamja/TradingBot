from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import git_workflow  # noqa: E402


def test_required_check_truth_is_explicit_when_ci_not_configured() -> None:
    truth = git_workflow.canonical_required_check_truth(verification_authority_profile="local_only")

    assert truth["verification_authority_profile"] == "local_only"
    assert truth["required_checks_configured"] is False
    assert truth["required_checks_discovered"] is False
    assert truth["required_checks_missing"] is False
    assert truth["required_checks_passed"] is True
    assert truth["verification_authority_satisfied"] is True


def test_wait_for_required_checks_detects_missing_required_checks() -> None:
    def runner(_cmd: list[str], check: bool = True):
        return SimpleNamespace(returncode=0, stdout="no checks reported on the branch", stderr="")

    result = git_workflow.wait_for_required_checks(
        runner,
        verification_authority_profile="local_plus_required_ci",
    )

    assert result.ok is False
    assert result.evidence["required_checks_configured"] is True
    assert result.evidence["required_checks_discovered"] is False
    assert result.evidence["required_checks_missing"] is True
    assert result.evidence["missing_required_checks_blocks_merge"] is True


def test_merge_flow_blocks_when_required_checks_fail() -> None:
    calls: list[list[str]] = []

    def runner(cmd: list[str], check: bool = True):
        calls.append(cmd)
        if cmd[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(returncode=0, stdout="created", stderr="")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout="build failed", stderr="")
        raise AssertionError(cmd)

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        verification_authority_profile="local_plus_required_ci",
    )

    assert result["post_task_decision"] == "failed_checks"
    assert result["required_checks_failed"] is True
    assert result["required_checks_passed"] is False
    assert result["verification_authority_satisfied"] is False
    assert result["next_task_may_proceed"] is False
    assert [cmd[:3] for cmd in calls] == [["gh", "pr", "create"], ["gh", "pr", "checks"]]


def test_merge_flow_requires_ci_even_when_local_acceptance_is_green() -> None:
    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(returncode=0, stdout="created", stderr="")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout="no checks reported on the branch", stderr="")
        raise AssertionError(cmd)

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        verification_authority_profile="local_plus_required_ci",
    )

    assert result["accepted"] is True
    assert result["required_checks_missing"] is True
    assert result["verification_authority_satisfied"] is False
    assert result["next_task_may_proceed"] is False


def test_merge_flow_can_succeed_with_required_ci_authority() -> None:
    calls: list[list[str]] = []

    def runner(cmd: list[str], check: bool = True):
        calls.append(cmd)
        if cmd[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(returncode=0, stdout="created", stderr="")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout="all checks passed", stderr="")
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        verification_authority_profile="required_ci_only",
    )

    assert result["verification_authority_profile"] == "required_ci_only"
    assert result["required_checks_discovered"] is True
    assert result["required_checks_passed"] is True
    assert result["verification_authority_satisfied"] is True
    assert result["merged_to_main"] is True
    assert result["clean_main_reset_completed"] is True
    assert result["next_task_may_proceed"] is True
