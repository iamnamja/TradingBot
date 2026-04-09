from __future__ import annotations

import json
from pathlib import Path
import sys
from types import SimpleNamespace

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import git_workflow  # noqa: E402


REPO_CHECK_CONTRACT = {
    "required_checks": ["ci-required"],
    "repo_check_contract_source": "tests",
}


def test_real_pr_required_check_smoke_proof_succeeds_for_open_pr(tmp_path: Path) -> None:
    artifact_path = tmp_path / "real_pr_smoke.json"

    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "pr", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 533,
                        "headRefName": "task-143-github-settle-window-and-dual-surface-probe",
                        "headRefOid": "abc123",
                        "baseRefName": "main",
                        "state": "OPEN",
                        "mergeStateStatus": "BLOCKED",
                        "url": "https://github.com/iamnamja/TradingBot/pull/533",
                    }
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    [
                        {
                            "type": "required_status_checks",
                            "ruleset_id": 13245426,
                            "ruleset_source": "repo:TradingBot",
                            "parameters": {
                                "required_status_checks": [{"context": "ci-required"}],
                                "strict_required_status_checks_policy": True,
                            },
                        }
                    ]
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/check-runs"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {"check_runs": [{"name": "ci", "status": "completed", "conclusion": "success"}]}
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/status"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {"state": "success", "statuses": [{"context": "ci-required", "state": "success"}]}
                ),
                stderr="",
            )
        raise AssertionError(cmd)

    truth = git_workflow.probe_real_pr_required_check_smoke_proof(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        artifact_path=str(artifact_path),
        settle_window_seconds=0,
    )

    assert truth["real_pr_required_check_smoke_proved"] is True
    assert truth["real_pr_required_check_smoke_reason"] == "smoke_proved"
    assert truth["pull_request_number"] == 533
    assert truth["pull_request_base_ref"] == "main"
    assert truth["pull_request_head_sha"] == "abc123"
    assert truth["required_check_truth"]["required_checks_passed"] is True
    assert truth["repo_required_check_enforcement_convergence"]["repo_required_check_enforcement_converged"] is True
    assert artifact_path.exists()


def test_real_pr_required_check_smoke_proof_reports_not_yet_reported_for_open_pr(tmp_path: Path) -> None:
    artifact_path = tmp_path / "real_pr_smoke_pending.json"

    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "pr", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 534,
                        "headRefName": "task-144-real-pr-required-check-smoke-proof",
                        "headRefOid": "def456",
                        "baseRefName": "main",
                        "state": "OPEN",
                        "mergeStateStatus": "BLOCKED",
                        "url": "https://github.com/iamnamja/TradingBot/pull/534",
                    }
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    [
                        {
                            "type": "required_status_checks",
                            "parameters": {
                                "required_status_checks": [{"context": "ci-required"}],
                                "strict_required_status_checks_policy": True,
                            },
                        }
                    ]
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/def456/check-runs"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"check_runs": []}), stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/def456/status"]:
            return SimpleNamespace(returncode=0, stdout=json.dumps({"state": "pending", "statuses": []}), stderr="")
        raise AssertionError(cmd)

    truth = git_workflow.probe_real_pr_required_check_smoke_proof(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        artifact_path=str(artifact_path),
        settle_window_seconds=0,
    )

    assert truth["real_pr_required_check_smoke_proved"] is False
    assert truth["real_pr_required_check_smoke_reason"] == "required_checks_not_yet_reported"
    assert truth["required_check_truth"]["required_checks_not_yet_reported"] is True
    assert truth["repo_required_check_enforcement_convergence"]["repo_required_check_enforcement_converged"] is True
    assert artifact_path.exists()


def test_real_pr_required_check_smoke_proof_blocks_when_pr_targets_non_default_branch(tmp_path: Path) -> None:
    artifact_path = tmp_path / "real_pr_smoke_wrong_base.json"

    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "pr", "view"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    {
                        "number": 535,
                        "headRefName": "task-144-real-pr-required-check-smoke-proof",
                        "headRefOid": "ghi789",
                        "baseRefName": "develop",
                        "state": "OPEN",
                        "mergeStateStatus": "BLOCKED",
                        "url": "https://github.com/iamnamja/TradingBot/pull/535",
                    }
                ),
                stderr="",
            )
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout=json.dumps(
                    [
                        {
                            "type": "required_status_checks",
                            "parameters": {
                                "required_status_checks": [{"context": "ci-required"}],
                                "strict_required_status_checks_policy": True,
                            },
                        }
                    ]
                ),
                stderr="",
            )
        raise AssertionError(cmd)

    truth = git_workflow.probe_real_pr_required_check_smoke_proof(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        artifact_path=str(artifact_path),
        settle_window_seconds=0,
    )

    assert truth["real_pr_required_check_smoke_proved"] is False
    assert truth["real_pr_required_check_smoke_reason"] == "pull_request_targets_non_default_branch"
    assert truth["pull_request_base_ref"] == "develop"
    assert artifact_path.exists()
