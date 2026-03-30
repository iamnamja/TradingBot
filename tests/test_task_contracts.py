from __future__ import annotations

import sys
from pathlib import Path

root = Path(__file__).resolve().parents[1]
if str(root) not in sys.path:
    sys.path.insert(0, str(root))

from agents.lib import task_contracts  # noqa: E402


def test_parse_required_files_from_both_supported_heading_styles() -> None:
    deliverables_task = """
## Deliverables
- `agents/run_task.py`
- `docs/ORCHESTRATOR_VISION_AND_CONTROLS.md`
"""
    exact_files_task = """
## Create or update these exact files
- `agents/lib/task_contracts.py`
- `docs/TRADINGBOT_PROJECT_STATE.md`
- `tasks/070a_orchestrator_exact_deliverable_parser_and_completion_gate.md`
- `README.md`
"""
    assert task_contracts.parse_required_files_from_task_text(deliverables_task) == ["agents/run_task.py", "docs/ORCHESTRATOR_VISION_AND_CONTROLS.md"]
    assert task_contracts.parse_required_files_from_task_text(exact_files_task) == ["agents/lib/task_contracts.py", "docs/TRADINGBOT_PROJECT_STATE.md", "tasks/070a_orchestrator_exact_deliverable_parser_and_completion_gate.md", "README.md"]


def test_parse_required_files_canonicalizes_root_narrative_docs() -> None:
    task_text = """
## Create or update these exact files
- `ORCHESTRATOR_PRODUCT_SPEC.md`
- `TRADINGBOT_PROJECT_STATE.md`
- `README.md`
"""
    assert task_contracts.parse_required_files_from_task_text(task_text) == ["docs/ORCHESTRATOR_PRODUCT_SPEC.md", "docs/TRADINGBOT_PROJECT_STATE.md", "README.md"]


def test_exact_deliverable_contract_rejects_traversal_and_absolute_paths() -> None:
    task_text = """
## Create or update these exact files
- `../outside.md`
- `/tmp/absolute.md`
- `https://example.com/file.md`
"""
    issues = task_contracts.exact_deliverable_contract_issues(task_text)
    assert any("path traversal" in issue for issue in issues)
    assert sum("repo-relative file path" in issue for issue in issues) >= 2


def test_exact_deliverable_contract_rejects_noncanonical_prefixes() -> None:
    task_text = """
## Create or update these exact files
- `notes/plan.md`
"""
    issues = task_contracts.exact_deliverable_contract_issues(task_text)
    assert issues == ["`notes/plan.md` is not under an allowed repo-relative path prefix."]
