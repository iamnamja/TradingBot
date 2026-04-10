from __future__ import annotations

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


def test_wait_for_required_checks_treats_no_checks_reported_as_not_yet_reported_non_success() -> None:
    def runner(_cmd: list[str], check: bool = True):
        return SimpleNamespace(returncode=0, stdout="no checks reported on the branch", stderr="")

    result = git_workflow.wait_for_required_checks(
        runner,
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result.ok is False
    assert result.message == "required checks not yet reported"
    assert result.evidence["required_checks_configured"] is True
    assert result.evidence["repo_check_contract_configured"] is True
    assert result.evidence["required_checks_discovered"] is False
    assert result.evidence["required_checks_not_yet_reported"] is True
    assert result.evidence["hosted_authority_probe_status"] == "not_yet_reported"
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
        if cmd[:3] == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="abc123", stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/check-runs"]:
            return SimpleNamespace(returncode=0, stdout='{"check_runs": []}', stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/status"]:
            return SimpleNamespace(returncode=0, stdout='{"state": "pending", "statuses": []}', stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(returncode=0, stdout='[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"ci-required"}],"strict_required_status_checks_policy":true}}]', stderr="")
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
    assert result["required_checks_not_yet_reported"] is True
    assert result["hosted_authority_probe_status"] == "not_yet_reported"
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
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout='[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"ci-required"}],"strict_required_status_checks_policy":true}}]',
                stderr="",
            )
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
    assert result["repo_required_checks"] == ("ci-required",)
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



def test_project_aware_authority_profiles_can_differ_across_projects() -> None:
    from agents.lib import project_registry  # noqa: E402

    tradingbot = project_registry.resolve_project_contract("tradingbot_monorepo")
    generic = project_registry.resolve_project_contract("generic_python_external")

    generic_truth = git_workflow.evaluate_project_verification_authority(
        project_contract=generic,
        local_validation_passed=True,
    )
    tradingbot_truth = git_workflow.evaluate_project_verification_authority(
        project_contract=tradingbot,
        local_validation_passed=True,
        required_check_truth=git_workflow.canonical_required_check_truth(
            verification_authority_profile="local_plus_required_ci",
            repo_check_contract=git_workflow.project_repo_check_contract(tradingbot),
            required_checks_discovered=False,
            hosted_checks_reported=False,
            hosted_authority_probe_status="misconfigured",
            hosted_authority_probe_note="Hosted checks did not report on the branch.",
        ),
    )

    assert generic_truth["verification_authority_profile"] == "local_only"
    assert generic_truth["verification_authority_satisfied"] is True
    assert generic_truth["hosted_authority_satisfied"] is True

    assert tradingbot_truth["verification_authority_profile"] == "local_plus_required_ci"
    assert tradingbot_truth["verification_authority_satisfied"] is False
    assert tradingbot_truth["required_check_truth"]["hosted_authority_probe_status"] == "misconfigured"


def test_project_merge_eligibility_blocks_when_hosted_authority_is_misconfigured() -> None:
    from agents.lib import project_registry  # noqa: E402

    tradingbot = project_registry.resolve_project_contract('tradingbot_monorepo')
    truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile='local_plus_required_ci',
        repo_check_contract=git_workflow.project_repo_check_contract(tradingbot),
        required_checks_discovered=False,
        hosted_checks_reported=False,
        hosted_authority_probe_status='misconfigured',
        hosted_authority_probe_note='Hosted checks did not report on the branch.',
    )

    eligibility = git_workflow.evaluate_project_merge_eligibility(
        project_contract=tradingbot,
        accepted=True,
        autonomous_merge_enabled=True,
        local_validation_passed=True,
        required_check_truth=truth,
    )

    assert eligibility['merge_eligible_now'] is False
    assert eligibility['merge_eligibility_reason'] == 'hosted_required_checks_misconfigured'
    assert eligibility['hosted_authority_convergence']['hosted_authority_converged'] is False


def test_project_merge_eligibility_succeeds_for_local_only_project_without_hosted_checks() -> None:
    from agents.lib import project_registry  # noqa: E402

    generic = project_registry.resolve_project_contract('generic_python_external')
    eligibility = git_workflow.evaluate_project_merge_eligibility(
        project_contract=generic,
        accepted=True,
        autonomous_merge_enabled=True,
        local_validation_passed=True,
    )

    assert eligibility['merge_eligible_now'] is True
    assert eligibility['merge_eligibility_reason'] == 'eligible'
    assert eligibility['hosted_authority_convergence']['hosted_authority_converged'] is True



def test_portfolio_scheduler_conservatively_stops_when_authority_unsatisfied() -> None:
    from agents.lib import project_registry  # noqa: E402

    tradingbot = project_registry.resolve_project_contract("tradingbot_monorepo")
    blocked_truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=git_workflow.project_repo_check_contract(tradingbot),
        required_checks_discovered=False,
        hosted_checks_reported=False,
        hosted_authority_probe_status="misconfigured",
    )
    eligibility = git_workflow.evaluate_project_merge_eligibility(
        project_contract=tradingbot,
        accepted=True,
        autonomous_merge_enabled=True,
        local_validation_passed=True,
        required_check_truth=blocked_truth,
    )

    assert eligibility["merge_eligible_now"] is False
    assert eligibility["next_task_may_proceed"] is False



def test_operational_convergence_reports_no_checks_reported_as_not_ready() -> None:
    truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_checks_discovered=False,
        hosted_checks_reported=False,
        hosted_authority_probe_status="misconfigured",
    )
    operational = git_workflow.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_check_truth=truth,
    )

    assert operational["unattended_execution_ready"] is False
    assert operational["operational_convergence_ready"] is False
    assert operational["operational_convergence_reason"] == "hosted_checks_not_reporting"


def test_operational_convergence_reports_green_required_checks_as_ready() -> None:
    truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_checks_discovered=True,
        hosted_checks_reported=True,
        hosted_authority_probe_status="satisfied",
    )
    operational = git_workflow.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_check_truth=truth,
    )

    assert operational["unattended_execution_ready"] is True
    assert operational["operational_convergence_ready"] is True
    assert operational["operational_convergence_reason"] == "ready"


def test_task_136_operational_convergence_reproof_blocks_progress_when_checks_do_not_report() -> None:
    from agents.lib import project_registry  # noqa: E402

    tradingbot = project_registry.resolve_project_contract("tradingbot_monorepo")
    truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=git_workflow.project_repo_check_contract(tradingbot),
        required_checks_discovered=False,
        hosted_checks_reported=False,
        hosted_authority_probe_status="misconfigured",
    )
    operational = git_workflow.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=git_workflow.project_repo_check_contract(tradingbot),
        required_check_truth=truth,
    )
    eligibility = git_workflow.evaluate_project_merge_eligibility(
        project_contract=tradingbot,
        accepted=True,
        autonomous_merge_enabled=True,
        local_validation_passed=True,
        required_check_truth=truth,
    )

    assert operational["unattended_execution_ready"] is False
    assert operational["operational_convergence_reason"] == "hosted_checks_not_reporting"
    assert eligibility["merge_eligible_now"] is False
    assert eligibility["next_task_may_proceed"] is False


def test_probe_repo_required_check_enforcement_parses_branch_rules_required_context() -> None:
    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout='[{"type":"required_status_checks","ruleset_id":42,"ruleset_source":"repo:TradingBot","parameters":{"required_status_checks":[{"context":"ci-required"}],"strict_required_status_checks_policy":true}}]',
                stderr="",
            )
        raise AssertionError(cmd)

    truth = git_workflow.probe_repo_required_check_enforcement(
        runner,
        repo_check_contract=REPO_CHECK_CONTRACT,
    )
    convergence = git_workflow.evaluate_repo_required_check_convergence(
        repo_check_contract=REPO_CHECK_CONTRACT,
        repo_enforcement_truth=truth,
    )

    assert truth["enforcement_source"] == "github_branch_rules"
    assert truth["required_status_check_contexts"] == ("ci-required",)
    assert truth["repo_required_check_enforcement_converged"] is True
    assert convergence["repo_required_check_enforcement_reason"] == "converged"


def test_probe_repo_required_check_enforcement_falls_back_to_branch_protection() -> None:
    calls: list[list[str]] = []

    def runner(cmd: list[str], check: bool = True):
        calls.append(cmd)
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(returncode=0, stdout='[]', stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/branches/main/protection"]:
            return SimpleNamespace(
                returncode=0,
                stdout='{"required_status_checks":{"strict":true,"contexts":["ci-required"]}}',
                stderr="",
            )
        raise AssertionError(cmd)

    truth = git_workflow.probe_repo_required_check_enforcement(
        runner,
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert truth["enforcement_source"] == "github_branch_protection"
    assert truth["branch_protection_enabled"] is True
    assert truth["required_status_check_contexts"] == ("ci-required",)
    assert truth["repo_required_check_enforcement_converged"] is True
    assert calls == [
        ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"],
        ["gh", "api", "repos/{owner}/{repo}/branches/main/protection"],
    ]


def test_operational_convergence_blocks_when_github_is_not_enforcing_ci_required() -> None:
    required_truth = git_workflow.canonical_required_check_truth(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_checks_discovered=True,
        hosted_checks_reported=True,
        required_checks_passed=True,
        hosted_authority_probe_status="satisfied",
    )
    enforcement_truth = git_workflow.canonical_repo_enforcement_truth(
        repo_check_contract=REPO_CHECK_CONTRACT,
        enforcement_probe_available=True,
        enforcement_probe_status="required_check_context_missing",
        enforcement_source="github_branch_rules",
        required_status_checks_rule_present=True,
        required_status_check_contexts=("different-check",),
    )
    operational = git_workflow.evaluate_hosted_authority_operational_convergence(
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
        required_check_truth=required_truth,
        repo_enforcement_truth=enforcement_truth,
    )

    assert operational["required_checks_discovered"] is True
    assert operational["repo_required_check_enforcement_converged"] is False
    assert operational["unattended_execution_ready"] is False
    assert operational["operational_convergence_reason"] == "required_check_enforcement_context_mismatch"


def test_merge_flow_stops_when_required_checks_pass_but_enforcement_is_not_converged() -> None:
    calls: list[list[str]] = []

    def runner(cmd: list[str], check: bool = True):
        calls.append(cmd)
        if cmd[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(returncode=0, stdout="created", stderr="")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout="all checks passed", stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(
                returncode=0,
                stdout='[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"wrong-check"}]}}]',
                stderr="",
            )
        raise AssertionError(cmd)

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="x",
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert result["required_checks_passed"] is True
    assert result["repo_required_check_enforcement"]["repo_required_check_enforcement_converged"] is False
    assert result["operational_convergence_reason"] == "required_check_enforcement_context_mismatch"
    assert result["merged_to_main"] is False
    assert result["next_task_may_proceed"] is False



def test_task_148_operator_proof_bundle_does_not_override_hosted_authority_truth() -> None:
    import importlib
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    if "agents.run_single_task" in sys.modules:
        del sys.modules["agents.run_single_task"]
    runner = importlib.import_module("agents.run_single_task")

    bundle = runner.build_live_canary_operator_proof_bundle(
        real_pr_smoke={
            "required_check_contract_status": "required_context_missing",
            "required_check_context": "ci-required",
            "note": "Required status check did not appear on the PR head SHA.",
        },
        safe_result={
            "task_path": "tasks/148_safe.md",
            "entry": {
                "final_decision": "completed",
                "validation": {"execution_invoked": True},
                "admission": {"autonomous_single_task_lane": "autonomous_safe"},
            },
            "ledger_path": "artifacts/autonomous_single_task/run_ledger.jsonl",
            "canary_metrics": {"total_runs": 2, "completed_runs": 1},
            "recovery_report": {"handoff_required_count": 1, "escalation_required_count": 1},
        },
        escalation_result={
            "task_path": "tasks/148_escalation.md",
            "entry": {
                "final_decision": "escalation_required",
                "admission": {"autonomous_single_task_lane": "escalation_required"},
                "escalation": {"required": True},
            },
            "supervised_handoff": {
                "handoff_required": True,
                "handoff_kind": "escalation_required",
                "implicated_paths": ["agents/run_task.py"],
            },
            "canary_metrics": {"total_runs": 2, "completed_runs": 1},
            "recovery_report": {"handoff_required_count": 1, "escalation_required_count": 1},
        },
        generated_at="2026-04-09T22:30:00Z",
    )

    assert bundle["bounded_claim_ready"] is False
    assert "real_github_required_check_not_yet_satisfied" in bundle["claim_blockers"]
    assert bundle["operator_next_action"].startswith("Do not widen autonomy claims")


def test_task_153_reliability_reproof_does_not_override_required_ci_authority_truth() -> None:
    reproof_scoreboard = {
        "pass_rate": 0.6667,
        "completed_runs": 4,
        "completed_after_self_heal_runs": 2,
        "non_completion_runs": 2,
    }

    def runner(cmd: list[str], check: bool = True):
        if cmd[:3] == ["gh", "pr", "create"]:
            return SimpleNamespace(returncode=0, stdout="created", stderr="")
        if cmd[:3] == ["gh", "pr", "checks"]:
            return SimpleNamespace(returncode=0, stdout="no checks reported on the branch", stderr="")
        if cmd[:3] == ["git", "rev-parse", "HEAD"]:
            return SimpleNamespace(returncode=0, stdout="abc123", stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/check-runs"]:
            return SimpleNamespace(returncode=0, stdout='{"check_runs": []}', stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/commits/abc123/status"]:
            return SimpleNamespace(returncode=0, stdout='{"state": "pending", "statuses": []}', stderr="")
        if cmd[:3] == ["gh", "api", "repos/{owner}/{repo}/rules/branches/main"]:
            return SimpleNamespace(returncode=0, stdout='[{"type":"required_status_checks","parameters":{"required_status_checks":[{"context":"ci-required"}],"strict_required_status_checks_policy":true}}]', stderr="")
        raise AssertionError(cmd)

    result = git_workflow.accepted_task_pr_merge_flow(
        runner,
        accepted=True,
        autonomous_merge_enabled=True,
        pr_title="task-153-reproof",
        verification_authority_profile="local_plus_required_ci",
        repo_check_contract=REPO_CHECK_CONTRACT,
    )

    assert reproof_scoreboard["pass_rate"] >= 0.6
    assert result["required_checks_not_yet_reported"] is True
    assert result["hosted_authority_probe_status"] == "not_yet_reported"
    assert result["verification_authority_satisfied"] is False
    assert result["next_task_may_proceed"] is False

