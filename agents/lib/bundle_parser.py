from __future__ import annotations

from typing import Callable, Dict, List, Pattern, Type


def parse_file_bundle(
    *,
    text: str,
    normalize_newlines: Callable[[str], str],
    file_bundle_begin: str,
    file_bundle_end: str,
    file_header_re: Pattern[str],
    file_end: str,
    error_cls: Type[Exception],
) -> Dict[str, str]:
    text = normalize_newlines(text)

    if file_bundle_begin not in text or file_bundle_end not in text:
        raise error_cls("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    start = text.index(file_bundle_begin) + len(file_bundle_begin)
    end = text.index(file_bundle_end)
    body = text[start:end].strip("\n")

    if not body.strip():
        return {}

    if "FILE:" not in body:
        raise error_cls("No FILE: headers found inside file bundle.")

    files: Dict[str, str] = {}
    lines = body.split("\n")
    i = 0
    while i < len(lines):
        m = file_header_re.match(lines[i])
        if not m:
            i += 1
            continue

        relpath = m.group(1).strip()
        if not relpath:
            raise error_cls("Empty FILE: path.")

        i += 1
        buf: List[str] = []
        while i < len(lines) and lines[i].strip("\n") != file_end:
            if file_header_re.match(lines[i]):
                raise error_cls(
                    f"Nested FILE header encountered before END_FILE for {relpath}. "
                    "Every FILE block must be closed with END_FILE before the next FILE header."
                )
            buf.append(lines[i])
            i += 1
        if i >= len(lines):
            raise error_cls(f"Missing END_FILE for {relpath}.")

        i += 1
        files[relpath] = "\n".join(buf).rstrip("\n") + "\n"

    if not files:
        raise error_cls("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    return files


def parse_method_insertion_bundle(
    *,
    text: str,
    expected_path: str,
    expected_method_name: str,
    normalize_newlines: Callable[[str], str],
    method_insertion_begin: str,
    method_insertion_end: str,
    method_block_begin: str,
    method_block_end: str,
    file_bundle_begin: str,
    file_header_re: Pattern[str],
    file_end: str,
    validate_single_method_text: Callable[[str, str], str] | Callable[..., str],
    error_cls: Type[Exception],
) -> str:
    expected_path = str(expected_path)
    expected_method_name = str(expected_method_name)
    text = normalize_newlines(text)
    lines = text.split("\n")

    if method_insertion_begin not in text:
        if file_bundle_begin in text:
            raise error_cls(
                "Method insertion response used BEGIN_FILE_BUNDLE. Protected-file method mode requires BEGIN_METHOD_INSERTION / END_METHOD_INSERTION."
            )
        raise error_cls("Method insertion response did not include BEGIN_METHOD_INSERTION / END_METHOD_INSERTION markers.")

    begin_idx = next((i for i, line in enumerate(lines) if line.strip() == method_insertion_begin), None)
    if begin_idx is None:
        raise error_cls("Missing BEGIN_METHOD_INSERTION in method insertion bundle.")
    end_idx = next((i for i in range(begin_idx + 1, len(lines)) if lines[i].strip() == method_insertion_end), None)
    if end_idx is None:
        raise error_cls("Missing END_METHOD_INSERTION in method insertion bundle.")

    body_lines = lines[begin_idx + 1 : end_idx]
    target_file = None
    method_name = None
    i = 0
    while i < len(body_lines):
        line = body_lines[i].strip()
        if line.startswith("TARGET_FILE:"):
            target_file = line.split(":", 1)[1].strip().replace("\\", "/")
        elif line.startswith("METHOD_NAME:"):
            method_name = line.split(":", 1)[1].strip()
        elif line == method_block_begin:
            i += 1
            buf: List[str] = []
            while i < len(body_lines) and body_lines[i].strip() != method_block_end:
                if body_lines[i].strip() == file_end or file_header_re.match(body_lines[i]):
                    raise error_cls("Malformed method insertion block: encountered file-bundle markers inside BEGIN_METHOD/END_METHOD.")
                buf.append(body_lines[i])
                i += 1
            if i >= len(body_lines):
                raise error_cls("Missing END_METHOD in method insertion bundle.")
            if target_file != expected_path:
                raise error_cls(f"Method insertion target file mismatch: expected {expected_path}, got {target_file}.")
            if method_name != expected_method_name:
                raise error_cls(f"Method insertion method mismatch: expected {expected_method_name}, got {method_name}.")
            payload = "\n".join(buf).rstrip("\n") + "\n"
            try:
                return validate_single_method_text(payload, expected_method_name, context="Method insertion bundle")  # type: ignore[misc]
            except TypeError:
                return validate_single_method_text(payload, expected_method_name)  # type: ignore[misc]
        i += 1

    raise error_cls("Method insertion response did not include BEGIN_METHOD / END_METHOD block.")


def parse_file_bundle_transport_resilient(
    *,
    text: str,
    expected_paths: List[str] | None,
    normalize_newlines: Callable[[str], str],
    file_bundle_begin: str,
    file_bundle_end: str,
    file_header_re: Pattern[str],
    bundle_file_header_re: Pattern[str],
    file_end: str,
    error_cls: Type[Exception],
) -> tuple[Dict[str, str], List[str]]:
    """Best-effort recovery for malformed outer file-bundle transport."""
    normalized = normalize_newlines(text)
    lines = normalized.split("\n")

    warnings: List[str] = []
    expected = {
        p.strip().replace("\\", "/")
        for p in (expected_paths or [])
        if isinstance(p, str) and p.strip()
    }

    begin_idxs = [i for i, line in enumerate(lines) if line.strip() == file_bundle_begin]
    end_idxs = [i for i, line in enumerate(lines) if line.strip() == file_bundle_end]

    markerless = False
    if begin_idxs and end_idxs:
        b = begin_idxs[0]
        e = end_idxs[-1]
        if e < b:
            raise error_cls("END_FILE_BUNDLE appears before BEGIN_FILE_BUNDLE.")
        inner = lines[b + 1 : e]
        if b > 0 and any(line.strip() for line in lines[:b]):
            warnings.append("ignored leading non-bundle text before BEGIN_FILE_BUNDLE")
        if e + 1 < len(lines) and any(line.strip() for line in lines[e + 1 :]):
            warnings.append("ignored trailing non-bundle text after END_FILE_BUNDLE")
    elif not begin_idxs and not end_idxs:
        inner = lines
        markerless = True
        warnings.append("recovered markerless file bundle transport (missing outer BEGIN_FILE_BUNDLE/END_FILE_BUNDLE)")
    else:
        raise error_cls("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    files: Dict[str, str] = {}
    cur_path: str | None = None
    cur_lines: List[str] = []
    saw_file = False
    trailing_text_ignored = False

    def _normalize_path(raw_path: str) -> str:
        return raw_path.strip().replace("\\", "/")

    def close_current(reason: str) -> None:
        nonlocal cur_path, cur_lines
        if cur_path is None:
            return
        files[cur_path] = "\n".join(cur_lines).rstrip("\n") + "\n"
        warnings.append(f"{reason}: {cur_path}")
        cur_path = None
        cur_lines = []

    def _next_meaningful(index: int) -> tuple[str | None, str | None]:
        j = index + 1
        while j < len(inner):
            candidate = inner[j]
            stripped = candidate.strip()
            if not stripped:
                j += 1
                continue
            if markerless and stripped in {"```", "~~~"}:
                j += 1
                continue
            return stripped, candidate
        return None, None

    def _should_treat_header_as_new_file(path: str) -> bool:
        return not expected or path in expected

    def _should_close_on_end_file(index: int) -> bool:
        next_stripped, next_raw = _next_meaningful(index)
        if next_stripped is None:
            return True
        if markerless:
            return True
        if next_raw is not None:
            header = bundle_file_header_re.match(next_raw)
            if header:
                next_path = _normalize_path(header.group(1))
                return _should_treat_header_as_new_file(next_path)
        return False

    i = 0
    while i < len(inner):
        line = inner[i]
        stripped = line.strip()

        if cur_path is None:
            if not stripped:
                i += 1
                continue
            if markerless and stripped in {"```", "~~~"}:
                i += 1
                continue
            if stripped in {file_bundle_begin, file_bundle_end}:
                warnings.append(f"ignored stray bundle marker outside FILE block: {stripped}")
                i += 1
                continue

            m = bundle_file_header_re.match(line)
            if not m:
                if markerless:
                    if saw_file:
                        trailing_text_ignored = True
                    i += 1
                    continue
                warnings.append(f"ignored non-bundle text outside FILE block: {stripped[:80]}")
                i += 1
                continue

            path = _normalize_path(m.group(1))
            if not path:
                raise error_cls("Empty FILE path.")
            if expected and path not in expected:
                warnings.append(f"ignored unexpected FILE header outside FILE block: {path}")
                i += 1
                continue
            if path in files:
                raise error_cls(f"Duplicate FILE path in bundle: {path}")
            cur_path = path
            cur_lines = []
            saw_file = True
            i += 1
            continue

        if stripped == file_end:
            if _should_close_on_end_file(i):
                close_current("closed explicit END_FILE")
                i += 1
                continue
            cur_lines.append(line)
            i += 1
            continue

        m = bundle_file_header_re.match(line)
        if m:
            next_path = _normalize_path(m.group(1))
            if _should_treat_header_as_new_file(next_path):
                close_current("auto-closed missing END_FILE before next FILE")
                continue
            cur_lines.append(line)
            i += 1
            continue

        cur_lines.append(line)
        i += 1

    if cur_path is not None:
        close_current("auto-closed missing trailing END_FILE at bundle end")

    if not files:
        raise error_cls("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    if trailing_text_ignored:
        warnings.append("ignored trailing non-bundle text after final FILE block")

    return files, warnings
