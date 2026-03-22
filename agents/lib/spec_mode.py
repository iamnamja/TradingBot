from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Dict, List

_VERIFICATION_CMD_RE = re.compile(r"^\s*-\s*`([^`]+)`\s*$")
_SECTION_HEADER_RE = re.compile(r"^\s{0,3}#{1,6}\s+(.*?)\s*$")
_BULLET_RE = re.compile(r"^\s*[-*]\s+(.*\S)\s*$")
_CODE_BLOCK_RE = re.compile(r"```(?:[^\n]*)\n(.*?)```", re.DOTALL)


def _normalize(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def _iter_sections(task_text: str) -> Dict[str, List[str]]:
    sections: Dict[str, List[str]] = {"": []}
    current = ""
    for line in _normalize(task_text).split("\n"):
        match = _SECTION_HEADER_RE.match(line)
        if match:
            current = match.group(1).strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)
    return sections


def _bullets(lines: List[str]) -> List[str]:
    out: List[str] = []
    for line in lines:
        match = _BULLET_RE.match(line)
        if match:
            out.append(match.group(1).strip())
    return out


def _capture_verification_commands(task_text: str) -> List[str]:
    sections = _iter_sections(task_text)
    commands: List[str] = []
    for name, lines in sections.items():
        if "verification" not in name and "acceptance" not in name and "goal" not in name:
            continue
        for line in lines:
            cmd_match = _VERIFICATION_CMD_RE.match(line)
            if cmd_match:
                commands.append(cmd_match.group(1).strip())
    if not commands:
        for code_block in _CODE_BLOCK_RE.findall(task_text):
            for candidate in _normalize(code_block).split("\n"):
                stripped = candidate.strip()
                if stripped.startswith(("pytest", "ruff", "python -m pytest", "python -m ruff")):
                    commands.append(stripped)
    return sorted(set(commands))


def _capture_forbidden_patterns(task_text: str) -> List[str]:
    sections = _iter_sections(task_text)
    patterns: List[str] = []
    for name, lines in sections.items():
        if "forbidden" in name or "do not" in name or "critical" in name:
            patterns.extend(_bullets(lines))
        else:
            for line in lines:
                normalized_line = line.strip().lower()
                if normalized_line.startswith("do not ") or normalized_line.startswith("never "):
                    patterns.append(line.strip())
    deduped = sorted({item for item in patterns if item})
    return deduped


def _capture_acceptance_criteria(task_text: str) -> List[str]:
    sections = _iter_sections(task_text)
    items: List[str] = []
    for name, lines in sections.items():
        if "acceptance criteria" in name or "required behavior" in name or "test requirements" in name:
            items.extend(_bullets(lines))
    return sorted({item for item in items if item})


def _capture_expected_outputs(task_text: str) -> List[str]:
    sections = _iter_sections(task_text)
    out: List[str] = []
    for name, lines in sections.items():
        if "expected output" in name or "output requirements" in name:
            out.extend(_bullets(lines))
    return sorted({item for item in out if item})


def _capture_scope(task_text: str) -> Dict[str, List[str]]:
    sections = _iter_sections(task_text)
    in_scope: List[str] = []
    out_of_scope: List[str] = []
    for name, lines in sections.items():
        lower_name = name.lower()
        bullets = _bullets(lines)
        if "goal" in lower_name or "required behavior" in lower_name or "deliverables" in lower_name:
            in_scope.extend(bullets)
        if "out of scope" in lower_name or "forbidden" in lower_name:
            out_of_scope.extend(bullets)
    return {
        "in_scope": sorted({item for item in in_scope if item}),
        "out_of_scope": sorted({item for item in out_of_scope if item}),
    }


def _capture_edge_cases(task_text: str) -> List[str]:
    lines = _normalize(task_text).split("\n")
    edge_cases: List[str] = []
    for line in lines:
        lowered = line.strip().lower()
        if "edge case" in lowered or "compatibility" in lowered or "must preserve" in lowered:
            if line.strip():
                edge_cases.append(line.strip())
    return sorted({item for item in edge_cases})


def task_is_underspecified(task_text: str) -> bool:
    text = _normalize(task_text)
    acceptance = _capture_acceptance_criteria(text)
    verification = _capture_verification_commands(text)
    scope = _capture_scope(text)
    return not acceptance or not verification or not scope["in_scope"]


def build_frozen_spec_artifact(task_text: str, task_path: str, *, force: bool = False) -> Dict[str, object]:
    normalized = _normalize(task_text)
    scope = _capture_scope(normalized)
    artifact = {
        "mode": "spec",
        "task_path": task_path,
        "source_hash": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
        "underspecified": task_is_underspecified(normalized),
        "forced": bool(force),
        "frozen_spec": {
            "scope": scope,
            "edge_cases": _capture_edge_cases(normalized),
            "forbidden_patterns": _capture_forbidden_patterns(normalized),
            "acceptance_criteria": _capture_acceptance_criteria(normalized),
            "verification_commands": _capture_verification_commands(normalized),
            "expected_outputs": _capture_expected_outputs(normalized),
        },
    }
    artifact["artifact_path"] = "artifacts/spec_mode/frozen_spec.json"
    return artifact


def write_frozen_spec_artifact(artifact: Dict[str, object], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(artifact, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
