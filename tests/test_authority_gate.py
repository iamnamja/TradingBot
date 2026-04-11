from agents.lib.authority_gate import (
    AuthorityEvidenceCategory,
    AuthorityGateDecision,
    classify_authority_evidence,
    decide_authority_gate,
)


def test_explicit_required_check_failure_classification_and_decision():
    evidence = {
        "required_checks": [
            {"name": "ci/build", "required": True, "status": "failed"},
            {"name": "lint", "required": True, "status": "success"},
        ]
    }
    category = classify_authority_evidence(evidence)
    assert category == AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE

    decision = decide_authority_gate(evidence)
    assert isinstance(decision, AuthorityGateDecision)
    assert decision.hard_block is True
    assert decision.suggest_retry is False
    assert decision.category == AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE
    assert "Explicit failure" in decision.reason


def test_policy_block_classification_and_decision():
    evidence = {"policy": {"block": True, "reason": "protected_branch"}}
    category = classify_authority_evidence(evidence)
    assert category == AuthorityEvidenceCategory.POLICY_BLOCK

    decision = decide_authority_gate(evidence)
    assert decision.hard_block is True
    assert decision.suggest_retry is False
    assert decision.category == AuthorityEvidenceCategory.POLICY_BLOCK
    assert "Policy indicates a blocking violation" in decision.reason


def test_no_checks_reported_prefers_bounded_retry():
    evidence = {}
    category = classify_authority_evidence(evidence)
    assert category == AuthorityEvidenceCategory.NO_CHECKS_REPORTED

    decision = decide_authority_gate(evidence)
    assert decision.hard_block is False
    assert decision.suggest_retry is True
    assert decision.retry_limit == 1
    assert decision.category == AuthorityEvidenceCategory.NO_CHECKS_REPORTED


def test_ambiguous_or_missing_evidence_prefers_bounded_retry():
    # A failed check that is not required should be treated as ambiguous
    evidence = {"checks": [{"name": "optional-docs", "required": False, "status": "failed"}]}
    category = classify_authority_evidence(evidence)
    assert category == AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE

    decision = decide_authority_gate(evidence)
    assert decision.hard_block is False
    assert decision.suggest_retry is True
    assert decision.retry_limit == 1
    assert decision.category == AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE
