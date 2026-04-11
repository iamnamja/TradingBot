from agents.lib.authority_gate import (
    AuthorityEvidenceCategory,
    classify_authority_evidence,
    should_hard_block,
)


def test_explicit_required_check_failure_blocks():
    evidence = {
        "required_checks": [
            {"name": "ci", "status": "failed", "required": True},
            {"name": "lint", "status": "success", "required": True},
        ]
    }
    decision = classify_authority_evidence(evidence)
    assert decision.category == AuthorityEvidenceCategory.EXPLICIT_REQUIRED_CHECK_FAILURE
    assert decision.hard_block is True
    assert should_hard_block(evidence) is True


def test_policy_block_blocks():
    evidence = {"policy_block": True}
    decision = classify_authority_evidence(evidence)
    assert decision.category == AuthorityEvidenceCategory.POLICY_BLOCK
    assert decision.hard_block is True
    assert should_hard_block(evidence) is True


def test_ambiguous_evidence_does_not_block():
    evidence = {"checks": [{"name": "ci", "status": "unknown"}]}
    decision = classify_authority_evidence(evidence)
    assert decision.category == AuthorityEvidenceCategory.AMBIGUOUS_OR_MISSING_EVIDENCE
    assert decision.hard_block is False
    assert should_hard_block(evidence) is False


def test_no_checks_reported_does_not_block():
    for ev in (None, {}, ""):
        decision = classify_authority_evidence(ev)
        assert decision.category == AuthorityEvidenceCategory.NO_CHECKS_REPORTED
        assert decision.hard_block is False
        assert should_hard_block(ev) is False


def test_string_policy_block_detection():
    text = "Merge blocked by policy: pending approval"
    decision = classify_authority_evidence(text)
    assert decision.category == AuthorityEvidenceCategory.POLICY_BLOCK
    assert decision.hard_block is True
