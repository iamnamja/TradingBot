from pathlib import Path


def test_run_task_wires_authority_gate_into_wait_for_required_checks() -> None:
    text = Path("agents/run_task.py").read_text(encoding="utf-8")

    assert "def classify_authority_evidence(" in text
    assert "def decide_authority_gate(" in text
    assert "classification = classify_authority_evidence(" in text
    assert "decision = decide_authority_gate(" in text
    assert 'evidence["authority_evidence_category"]' in text
    assert 'evidence["authority_gate_decision"]' in text
