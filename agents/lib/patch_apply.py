from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Dict, List, Type

PATCH_APPLY_BEGIN = "BEGIN_PATCH_APPLY"
PATCH_APPLY_END = "END_PATCH_APPLY"
CONTENT_BEGIN = "BEGIN_CONTENT"
CONTENT_END = "END_CONTENT"

CODEX_BEGIN = "*** Begin Patch"
CODEX_END = "*** End Patch"


@dataclass(frozen=True)
class PatchApplyOperation:
    kind: str
    path: str
    content: str | None = None


def _normalize_path(path: str) -> str:
    return str(path or "").strip().replace("\\", "/")


def _normalize_content(text: str) -> str:
    return text.rstrip("\n") + "\n"


def _strip_apply_patch_wrapper(text: str, normalize_newlines: Callable[[str], str]) -> str:
    normalized = normalize_newlines(text)
    match = re.search(
        r"apply_patch\s*<<['\"]?PATCH['\"]?\n(?P<body>.*?)(?:\nPATCH\s*)$",
        normalized,
        re.DOTALL,
    )
    if match:
        return match.group("body")
    return normalized


def looks_like_patch_apply_payload(*, text: str, normalize_newlines: Callable[[str], str]) -> bool:
    normalized = _strip_apply_patch_wrapper(text, normalize_newlines)
    return (PATCH_APPLY_BEGIN in normalized and PATCH_APPLY_END in normalized) or (
        CODEX_BEGIN in normalized and CODEX_END in normalized
    )


def parse_patch_apply_operations(*, text: str, normalize_newlines: Callable[[str], str], error_cls: Type[Exception]) -> List[PatchApplyOperation]:
    normalized = _strip_apply_patch_wrapper(text, normalize_newlines)
    if PATCH_APPLY_BEGIN in normalized and PATCH_APPLY_END in normalized:
        return _parse_normalized_payload(text=normalized, normalize_newlines=normalize_newlines, error_cls=error_cls)
    if CODEX_BEGIN in normalized and CODEX_END in normalized:
        return _parse_codex_style_payload(text=normalized, normalize_newlines=normalize_newlines, error_cls=error_cls)
    raise error_cls("Patch/apply payload missing recognized BEGIN/END markers.")


def _parse_normalized_payload(*, text: str, normalize_newlines: Callable[[str], str], error_cls: Type[Exception]) -> List[PatchApplyOperation]:
    text = normalize_newlines(text)
    start = text.index(PATCH_APPLY_BEGIN) + len(PATCH_APPLY_BEGIN)
    end = text.index(PATCH_APPLY_END)
    body = text[start:end].strip("\n")
    if not body.strip():
        raise error_cls("Patch/apply payload contained no operations.")

    lines = body.split("\n")
    i = 0
    out: List[PatchApplyOperation] = []
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("ADD_FILE:") or line.startswith("UPDATE_FILE:"):
            kind = "add" if line.startswith("ADD_FILE:") else "update"
            path = _normalize_path(line.split(":", 1)[1])
            if not path:
                raise error_cls("Patch/apply operation missing path.")
            i += 1
            if i >= len(lines) or lines[i].strip() != CONTENT_BEGIN:
                raise error_cls(f"Missing {CONTENT_BEGIN} for {path}.")
            i += 1
            buf: List[str] = []
            while i < len(lines) and lines[i].strip() != CONTENT_END:
                buf.append(lines[i])
                i += 1
            if i >= len(lines):
                raise error_cls(f"Missing {CONTENT_END} for {path}.")
            out.append(PatchApplyOperation(kind=kind, path=path, content=_normalize_content("\n".join(buf))))
            i += 1
            continue
        if line.startswith("DELETE_FILE:"):
            path = _normalize_path(line.split(":", 1)[1])
            if not path:
                raise error_cls("Patch/apply delete operation missing path.")
            out.append(PatchApplyOperation(kind="delete", path=path))
            i += 1
            continue
        raise error_cls(f"Unrecognized patch/apply operation line: {line}")

    if not out:
        raise error_cls("Patch/apply payload contained no operations.")
    return out


def _parse_codex_style_payload(*, text: str, normalize_newlines: Callable[[str], str], error_cls: Type[Exception]) -> List[PatchApplyOperation]:
    text = normalize_newlines(text)
    start = text.index(CODEX_BEGIN) + len(CODEX_BEGIN)
    end = text.index(CODEX_END)
    body = text[start:end].strip("\n")
    lines = body.split("\n") if body else []

    i = 0
    out: List[PatchApplyOperation] = []
    while i < len(lines):
        raw = lines[i]
        stripped = raw.strip()
        if not stripped:
            i += 1
            continue
        if stripped.startswith("*** Add File:"):
            path = _normalize_path(stripped.split(":", 1)[1])
            i += 1
            buf: List[str] = []
            while i < len(lines) and not lines[i].startswith("*** "):
                line = lines[i]
                buf.append(line[1:] if line.startswith("+") else line)
                i += 1
            out.append(PatchApplyOperation(kind="add", path=path, content=_normalize_content("\n".join(buf))))
            continue
        if stripped.startswith("*** Update File:"):
            path = _normalize_path(stripped.split(":", 1)[1])
            i += 1
            buf: List[str] = []
            while i < len(lines) and not lines[i].startswith("*** "):
                line = lines[i]
                marker = line.strip()
                if marker.startswith("@@"):
                    i += 1
                    continue
                if line.startswith("-"):
                    i += 1
                    continue
                if line.startswith("+") or line.startswith(" "):
                    buf.append(line[1:])
                else:
                    buf.append(line)
                i += 1
            out.append(PatchApplyOperation(kind="update", path=path, content=_normalize_content("\n".join(buf))))
            continue
        if stripped.startswith("*** Delete File:"):
            path = _normalize_path(stripped.split(":", 1)[1])
            out.append(PatchApplyOperation(kind="delete", path=path))
            i += 1
            continue
        raise error_cls(f"Unrecognized codex-style patch operation line: {raw}")

    if not out:
        raise error_cls("Codex-style patch/apply payload contained no operations.")
    return out


def materialize_patch_apply_operations(*, operations: List[PatchApplyOperation], existing_files: Dict[str, str] | None = None, normalize_newlines: Callable[[str], str] | None = None, error_cls: Type[Exception] = ValueError) -> Dict[str, str]:
    normalize = normalize_newlines or (lambda value: str(value or "").replace("\r\n", "\n").replace("\r", "\n"))
    files: Dict[str, str] = {}
    for path, content in dict(existing_files or {}).items():
        norm_path = _normalize_path(path)
        if norm_path:
            files[norm_path] = _normalize_content(normalize(content))

    for op in operations:
        path = _normalize_path(op.path)
        if not path:
            raise error_cls("Patch/apply operation missing normalized path.")
        if op.kind == "delete":
            files.pop(path, None)
            continue
        if op.content is None:
            raise error_cls(f"Patch/apply {op.kind} operation for {path} missing content.")
        files[path] = _normalize_content(normalize(op.content))
    return files


def materialize_patch_apply_payload(*, text: str, existing_files: Dict[str, str] | None = None, normalize_newlines: Callable[[str], str], error_cls: Type[Exception]) -> Dict[str, str]:
    operations = parse_patch_apply_operations(text=text, normalize_newlines=normalize_newlines, error_cls=error_cls)
    return materialize_patch_apply_operations(
        operations=operations,
        existing_files=existing_files,
        normalize_newlines=normalize_newlines,
        error_cls=error_cls,
    )
