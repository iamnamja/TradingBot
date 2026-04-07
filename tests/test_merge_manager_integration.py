from __future__ import annotations

from pathlib import Path
import sys
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import git_workflow  # noqa: E402


REPO_CHECK_CONTRACT = {
    "required_checks": ["ci"],
    "repo_check_contract_source": "tests",
}


def test_required_check_truth_is_explicit_when_ci_not_configured() -> None:
    truth = git_workflow.canonical_required_check_truth(verification_authority_profile="local_only")

    assert truth["verification_authority_profile"] == "local_only"
    assert truth["required_checks_configured"] is False
    assert truth["repo_check_contract_configured"] is False
    assert truth["repo_required_checks"] == ()
    assert truth["required_checks_discovered"] is False
    assert truth["required_checks_missing"] is False
    assert truth["required_checks_passed"] is True
    assert truth["hosted_authority_probe_status"] == "not_required"
    assert truth["verification_authority_satisfied"] is True


def test_wait_for_required_checks_treats_no_checks_reported_as_misconfigured_non_success() -> None:
    def runner(_cmd: list[str], check: bool = True):
        return SimpleNamespace(returncode=0, stdout="no checks reported on the branch", stderr="")

    result = git_workflow.wait_for_required_checks(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result.ok is False
    assert result.message == "required checks misconfigured"
    assert result.evidence["required_checks_configured"] is True
    assert result.evidence["repo_check_contract_configured"] is True
    assert result.evidence["required_checks_discovered"] is False
    assert result.evidence["required_checks_misconfigured"] is True
    assert result.evidence["hosted_authority_probe_status"] == "misconfigured"
    assert result.evidence["hosted_authority_satisfied"] is False


def test_wait_for_required_checks_distinguishes_unavailable_probe() -> None:
    def runner(_cmd: list[str], check: bool = True):
        raise RuntimeError("gh cli unavailable")

    result = git_workflow.wait_for_required_checks(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result.ok is False
    assert result.message == "hosted authority probe unavailable"
    assert result.evidence["required_checks_unavailable"] is True
    assert result.evidence["hosted_authority_probe_status"] == "unavailable"
    assert result.evidence["hosted_authority_available"] is False


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
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result["post_task_decision"] == "failed_checks"
    assert result["required_checks_failed"] is True
    assert result["required_checks_passed"] is False
    assert result["hosted_authority_probe_status"] == "reported_unsatisfied"
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
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result["accepted"] is True
    assert result["required_checks_misconfigured"] is True
    assert result["hosted_authority_probe_status"] == "misconfigured"
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
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result["verification_authority_profile"] == "required_ci_only"
    assert result["repo_check_contract_configured"] is True
    assert result["repo_required_checks"] == ("ci",)
    assert result["required_checks_discovered"] is True
    assert result["required_checks_passed"] is True
    assert result["hosted_checks_source"] == "gh_pr_checks"
    assert result["hosted_authority_probe_status"] == "satisfied"
    assert result["hosted_authority_available"] is True
    assert result["hosted_authority_satisfied"] is True
    assert result["verification_authority_satisfied"] is True
    assert result["merged_to_main"] is True
    assert result["clean_main_reset_completed"] is True
    assert result["next_task_may_proceed"] is True
