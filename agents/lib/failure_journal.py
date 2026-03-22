from __future__ import annotations

import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_RAW_SNIPPET_LIMIT = 400
DEFAULT_JOURNAL_PATH = Path("artifacts/failure_journal.jsonl")
_FAILURE_COUNTS: Dict[str, int] = {}


def classify_failure(kind: str, message: str) -> str:
    text = f"{kind}\n{message}".lower()
    if "modulenotfounderror" in text or "imports" in text:
        return "imports"
    if "syntaxerror" in text or "python syntax" in text:
        return "python_syntax"
    if "ruff" in text or "lint" in text:
        return "lint"
    if "bundle" in text or "end_file" in text or "begin_file_bundle" in text:
        return "bundle_transport"
    if "policy" in text:
        return "policy_violation"
    if "pytest" in text or "assert " in text or "test_" in text:
        return "tests"
    return (kind or "unknown").strip() or "unknown"


def _normalize_failure_message(message: str) -> str:
    value = str(message or "")
    value = re.sub(r"'[^']*'", "'<value>'", value)
    value = re.sub(r'"[^"]*"', '"<value>"', value)
    value = re.sub(r"\b\d+\b", "<num>", value)
    value = re.sub(r"\s+", " ", value).strip().lower()
    return value


def failure_fingerprint(*, kind: str, message: str, category: str) -> str:
    payload = f"{category}|{kind}|{_normalize_failure_message(message)}".encode("utf-8", errors="replace")
    digest = hashlib.sha1(payload).hexdigest()[:12]
    return f"{category}:{digest}"


def bounded_failure_snippet(message: str, max_chars: int = DEFAULT_RAW_SNIPPET_LIMIT) -> str:
    value = str(message or "")
    limit = max(32, int(max_chars))
    if len(value) <= limit:
        return value
    suffix = "...[truncated]"
    head = value[: max(0, limit - len(suffix))]
    return f"{head}{suffix}"


def recommended_next_action(
    *,
    kind: str,
    message: str,
    category: str,
    retry_count: int,
    fingerprint: str,
    raw_failure_snippet: str,
) -> str:
    if retry_count >= 3:
        return "manual_patch"
    if category in {"bundle_transport", "policy_violation", "imports", "tests", "lint", "python_syntax"}:
        return "retry_with_targeted_fix"
    return "retry_with_targeted_fix"


def chosen_remediation_path(
    *,
    kind: str,
    message: str,
    category: str,
    retry_count: int,
    fingerprint: str,
    raw_failure_snippet: str,
    recommended_next_action: str,
) -> str:
    if retry_count >= 3:
        return "manual_patch"
    return recommended_next_action or "retry_with_targeted_fix"


def retry_count_for_fingerprint(fingerprint: str) -> int:
    count = int(_FAILURE_COUNTS.get(fingerprint, 0)) + 1
    _FAILURE_COUNTS[fingerprint] = count
    return count


def failure_journal_path() -> Path:
    raw = os.getenv("TRADINGBOT_FAILURE_JOURNAL_PATH", "").strip()
    if raw:
        return Path(raw)
    return DEFAULT_JOURNAL_PATH


def append_failure_journal_entry(entry: Dict[str, Any], journal_path: Path | str | None = None) -> None:
    path = Path(journal_path) if journal_path is not None else failure_journal_path()
    payload = dict(entry)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(payload, sort_keys=True) + "\n")


def read_failure_journal(journal_path: Path | str | None = None) -> List[Dict[str, Any]]:
    path = Path(journal_path) if journal_path is not None else failure_journal_path()
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows
