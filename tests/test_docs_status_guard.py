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

    assert extract_completed_through_task(readme_text) == 195
    assert extract_completed_through_task(state_text) == 195

    assert extract_active_tranche(readme_text) == (196, 200)
    assert extract_active_tranche(state_text) == (196, 200)
    assert extract_active_tranche(docs_readme_text) == (196, 200)


def test_validate_docs_status_ok_current_snapshot():
    ok, report = validate_docs_status(
        [Path("README.md"), Path("docs/README.md"), Path("docs/TRADINGBOT_PROJECT_STATE.md")]
    )
    assert ok is True
    assert report["completed_through"]["disagreements"] == []
    assert report["active_tranche"]["disagreements"] == []


def test_detects_completed_through_drift(tmp_path: Path):
    readme_text = Path("README.md").read_text(encoding="utf-8")
    if "complete through Task 195" in readme_text:
        mutated = readme_text.replace("complete through Task 195", "complete through Task 196")
    else:
        mutated = readme_text.replace("post-Task 195", "post-Task 196")

    mutated_path = tmp_path / "README.md"
    mutated_path.write_text(mutated, encoding="utf-8")

    ok, report = validate_docs_status([mutated_path, Path("docs/TRADINGBOT_PROJECT_STATE.md")])
    assert ok is False
    disagreements = report["completed_through"]["disagreements"]
    assert str(mutated_path) in disagreements


def test_detects_tranche_range_drift(tmp_path: Path):
    docs_readme_text = Path("docs/README.md").read_text(encoding="utf-8")

    if "196?200" in docs_readme_text:
        mutated = docs_readme_text.replace("196?200", "196?201")
    elif "196-200" in docs_readme_text:
        mutated = docs_readme_text.replace("196-200", "196-201")
    else:
        raise AssertionError("Current docs/README.md does not contain a parseable 196?200 or 196-200 active tranche range.")

    mutated_path = tmp_path / "docs_README.md"
    mutated_path.write_text(mutated, encoding="utf-8")

    ok, report = validate_docs_status([Path("README.md"), mutated_path, Path("docs/TRADINGBOT_PROJECT_STATE.md")])
    assert ok is False
    disagreements = report["active_tranche"]["disagreements"]
    assert str(mutated_path) in disagreements
