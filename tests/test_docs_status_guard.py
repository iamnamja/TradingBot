from pathlib import Path

from agents.lib.docs_status_guard import (
    extract_active_tranche,
    extract_completed_through_task,
    validate_docs_status,
)


def test_extractors_find_values_current_snapshot():
    readme_text = Path("README.md").read_text(encoding="utf-8")
    state_text = Path("docs/TRADINGBOT_PROJECT_STATE.md").read_text(encoding="utf-8")
    docs_readme_text = Path("docs/README.md").read_text(encoding="utf-8")

    # Completed-through should be 185 from README and state doc (accepting different phrasings)
    assert extract_completed_through_task(readme_text) == 186
    assert extract_completed_through_task(state_text) == 186

    # Active tranche should be 186–190 across docs (hyphen or en-dash both acceptable)
    assert extract_active_tranche(readme_text) == (186, 190)
    assert extract_active_tranche(state_text) == (186, 190)
    assert extract_active_tranche(docs_readme_text) == (186, 190)


def test_validate_docs_status_ok_current_snapshot():
    ok, report = validate_docs_status(
        [Path("README.md"), Path("docs/README.md"), Path("docs/TRADINGBOT_PROJECT_STATE.md")]
    )
    assert ok is True
    assert report["completed_through"]["disagreements"] == []
    assert report["active_tranche"]["disagreements"] == []


def test_detects_completed_through_drift(tmp_path: Path):
    # Create a modified README that incorrectly references a different "complete through Task" number
    readme_text = Path("README.md").read_text(encoding="utf-8")
    # Replace the specific "complete through Task 186" phrasing; fall back to "post-Task 186" if needed
    if "complete through Task 186" in readme_text:
        mutated = readme_text.replace("complete through Task 186", "complete through Task 187")
    else:
        mutated = readme_text.replace("post-Task 186", "post-Task 187")

    mutated_path = tmp_path / "README.md"
    mutated_path.write_text(mutated, encoding="utf-8")

    ok, report = validate_docs_status([mutated_path, Path("docs/TRADINGBOT_PROJECT_STATE.md")])
    assert ok is False
    disagreements = report["completed_through"]["disagreements"]
    assert str(mutated_path) in disagreements


def test_detects_tranche_range_drift(tmp_path: Path):
    # Create a modified docs/README that incorrectly references a different tranche end
    docs_readme_text = Path("docs/README.md").read_text(encoding="utf-8")
    # Change a "186–190" or "186-190" occurrence to "186–191" to simulate drift.
    # Handle both en-dash and ASCII hyphen cases.
    if "186–190" in docs_readme_text:
        mutated = docs_readme_text.replace("186–190", "186–191")
    else:
        mutated = docs_readme_text.replace("186-190", "186-191")

    mutated_path = tmp_path / "docs_README.md"
    mutated_path.write_text(mutated, encoding="utf-8")

    ok, report = validate_docs_status([Path("README.md"), mutated_path, Path("docs/TRADINGBOT_PROJECT_STATE.md")])
    assert ok is False
    disagreements = report["active_tranche"]["disagreements"]
    assert str(mutated_path) in disagreements
