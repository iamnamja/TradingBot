
from __future__ import annotations

import re
from typing import Callable, Dict, List, Pattern, Tuple


def parse_task_contract_directives(
    *,
    task_text: str,
    iter_markdown_sections: Callable[[str], List[Tuple[str, List[str]]]],
    contract_directive_re: Pattern[str],
) -> Dict[str, List[str]]:
    directives: Dict[str, List[str]] = {}
    allowed_sections = {"", "machine-readable contract directives", "critical", "current runner baseline — must match exactly"}
    for section_name, section_lines in iter_markdown_sections(task_text):
        if section_name not in allowed_sections and "contract" not in section_name:
            continue
        for raw_line in section_lines:
            m = contract_directive_re.match(raw_line)
            if not m:
                continue
            key = m.group(1).strip().upper()
            value = m.group(2).strip()
            directives.setdefault(key, []).append(value)
    return directives


def build_seam_manifest() -> Dict[str, object]:
    return {
        "invented_aliases": {
            "failure_journal_export": "_failure_journal_exports",
            "shell_router_export": "_shell_router_exports",
            "validator_runner_exports": "_validator_runner_exports",
            "_validator_runner_exports": None,
        },
        "allowed_failure_journal_keys": {
            "failure_journal",
            "classify_failure",
            "failure_fingerprint",
            "bounded_failure_snippet",
            "recommended_next_action",
            "chosen_remediation_path",
            "append_failure_journal_entry",
            "retry_count_for_fingerprint",
        },
        "forbidden_failure_journal_keys": {
            "write_failure_journal",
            "build_failure_journal_entry",
            "load_failure_journal_entries",
            "build_failure_entry",
        },
        "recursive_runner_patterns": (
            re.compile(r"\brun_task\.main\s*\("),
            re.compile(r"\brun_task\.run_task_shell\s*\("),
            re.compile(r"py\s+-m\s+agents\.run_task"),
            re.compile(r"pytest\s+-q"),
            re.compile(r"ruff\s+check\s+\."),
        ),
        "allowed_in_process_patterns": (
            re.compile(r"\bcheck_runner\.run_checks\s*\("),
            re.compile(r"\bvalidator_runner\._run_plugin_validators\s*\("),
        ),
    }


def _contains_identifier_token(text: str, token: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(token)}(?![A-Za-z0-9_])", text) is not None


def _contains_call_like(text: str, name: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9_]){re.escape(name)}\s*\(", text) is not None


def validate_seam_manifest_for_bundle(*, bundle: Dict[str, str], task_text: str) -> Dict[str, List[str]]:
    manifest = build_seam_manifest()
    issues: Dict[str, List[str]] = {}
    invented_aliases = manifest["invented_aliases"]
    allowed_failure_journal_keys = manifest["allowed_failure_journal_keys"]
    forbidden_failure_journal_keys = manifest["forbidden_failure_journal_keys"]
    recursive_runner_patterns = manifest["recursive_runner_patterns"]
    allowed_in_process_patterns = manifest["allowed_in_process_patterns"]

    for rel, content in bundle.items():
        if not rel.endswith('.py'):
            continue
        if not rel.startswith('tests/') and 'failure_journal' not in content and 'shell_router' not in content and 'validator_runner' not in content:
            continue
        rel_issues: List[str] = []
        for alias in invented_aliases:
            if _contains_identifier_token(content, alias):
                rel_issues.append(f"references invented seam alias `{alias}` not present in live exports")
        if any(p.search(content) for p in recursive_runner_patterns) and not any(p.search(content) for p in allowed_in_process_patterns):
            rel_issues.append("appears to invoke repo-wide validators recursively from generated tests")
        if _contains_call_like(content, '_failure_journal_exports'):
            for bad in sorted(forbidden_failure_journal_keys):
                if _contains_identifier_token(content, bad):
                    rel_issues.append(f"references non-live failure-journal export key `{bad}`")
            # if explicit string assertions against exports exist, enforce allowed key set
            for key in re.findall(r'"([A-Za-z_][A-Za-z0-9_]*)"\s+in\s+exports', content):
                if key not in allowed_failure_journal_keys:
                    rel_issues.append(f"references non-live failure-journal export key `{key}`")
        if rel_issues:
            issues.setdefault(rel, []).extend(rel_issues)
    return issues
