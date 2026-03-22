from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, List

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
    out: List[str] = []
    lower = _normalize(task_text).lower()
    if "do not" in lower:
        for line in _normalize(task_text).split("\n"):
            stripped = line.strip()
            if not stripped:
                continue
            if "do not" in stripped.lower() or "must not" in stripped.lower() or "forbid" in stripped.lower():
                out.append(stripped)
    return sorted(set(out))


def _capture_acceptance_criteria(task_text: str) -> List[str]:
    sections = _iter_sections(task_text)
    out: List[str] = []
    for name, lines in sections.items():
        if "acceptance" in name or "goal" in name or "requirements" in name:
            out.extend(_bullets(lines))
    if not out:
        out.extend(_bullets(_normalize(task_text).split("\n")))
    return sorted(set(x for x in out if x))


def _capture_expected_outputs(task_text: str) -> List[str]:
    outputs: List[str] = []
    sections = _iter_sections(task_text)
    for name, lines in sections.items():
        if "deliverable" in name or "output" in name:
            outputs.extend(_bullets(lines))
    return sorted(set(outputs))


def task_is_underspecified(task_text: str) -> bool:
    text = _normalize(task_text)
    if len(text.split()) < 80:
        return True
    has_acceptance = len(_capture_acceptance_criteria(task_text)) > 0
    has_verification = len(_capture_verification_commands(task_text)) > 0
    return not (has_acceptance and has_verification)


def build_frozen_spec_artifact(task_text: str, task_path: str, force: bool = False) -> Dict[str, Any]:
    normalized = _normalize(task_text)
    source_hash = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    verification_commands = _capture_verification_commands(task_text) or ["pytest -q", "ruff check ."]

    frozen_spec: Dict[str, Any] = {
        "scope": _capture_acceptance_criteria(task_text),
        "forbidden_patterns": _capture_forbidden_patterns(task_text),
        "acceptance_criteria": _capture_acceptance_criteria(task_text),
        "verification_commands": verification_commands,
        "expected_outputs": _capture_expected_outputs(task_text),
        "acceptance_bullets": _capture_acceptance_criteria(task_text),
        "deliverables_bullets": _capture_expected_outputs(task_text),
    }

    artifact: Dict[str, Any] = {
        "mode": "spec",
        "task_path": task_path,
        "source_hash": source_hash,
        "frozen_spec": frozen_spec,
        "verification_commands": verification_commands,
        "artifact_kind": "frozen_spec",
        "artifact_path": "artifacts/spec_mode/frozen_spec.json",
        "canonical_task_text": normalized,
        "frozen_spec_path": "artifacts/spec_mode/frozen_spec.json",
        "resolved_from_underspecified": bool(force),
    }
    return artifact


def write_frozen_spec_artifact(artifact: Dict[str, Any], out_path: Path) -> None:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8", newline="\n")


def read_frozen_spec_artifact(path: Path | str) -> Dict[str, Any]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Frozen spec artifact must be a JSON object.")
    return data


def resolve_execution_task_text(task_text: str, task_path: str | None = None) -> Dict[str, Any]:
    stripped = (task_text or "").strip()
    artifact: Dict[str, Any] | None = None
    artifact_path = task_path or ""

    if task_path:
        p = Path(task_path)
        if p.exists():
            try:
                data = read_frozen_spec_artifact(p)
                if isinstance(data, dict) and data.get("frozen_spec") is not None:
                    artifact = data
                    artifact_path = p.as_posix()
            except Exception:
                artifact = None

    if artifact is None:
        try:
            maybe = json.loads(stripped)
            if isinstance(maybe, dict) and maybe.get("frozen_spec") is not None:
                artifact = maybe
        except Exception:
            artifact = None

    if artifact is None:
        return {
            "task_text": task_text,
            "resolved_from_frozen": False,
            "artifact_path": artifact_path,
            "mode": "execution",
        }

    canonical = artifact.get("canonical_task_text")
    if not isinstance(canonical, str) or not canonical.strip():
        canonical = artifact.get("task_text")
    if not isinstance(canonical, str) or not canonical.strip():
        canonical = json.dumps(artifact.get("frozen_spec", {}), indent=2, sort_keys=True)

    return {
        "task_text": canonical,
        "resolved_from_frozen": True,
        "artifact_path": artifact_path or str(artifact.get("artifact_path", "")),
        "mode": "execution",
    }
