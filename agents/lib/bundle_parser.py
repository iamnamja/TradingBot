from __future__ import annotations

import re

from typing import Any, Callable, Dict, List, Pattern, Type, Tuple


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
    entries = parse_file_bundle_entries(
        text=text,
        normalize_newlines=normalize_newlines,
        file_bundle_begin=file_bundle_begin,
        file_bundle_end=file_bundle_end,
        file_header_re=file_header_re,
        file_end=file_end,
        error_cls=error_cls,
    )

    files: Dict[str, str] = {}
    for relpath, content in entries:
        if relpath in files:
            raise error_cls(f"Duplicate FILE path in bundle: {relpath}")
        files[relpath] = content

    if not files:
        raise error_cls("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    return files




def parse_file_bundle_entries(
    *,
    text: str,
    normalize_newlines: Callable[[str], str],
    file_bundle_begin: str,
    file_bundle_end: str,
    file_header_re: Pattern[str],
    file_end: str,
    error_cls: Type[Exception],
) -> List[Tuple[str, str]]:
    text = normalize_newlines(text)

    if file_bundle_begin not in text or file_bundle_end not in text:
        raise error_cls("Model output missing BEGIN_FILE_BUNDLE/END_FILE_BUNDLE markers.")

    start = text.index(file_bundle_begin) + len(file_bundle_begin)
    end = text.index(file_bundle_end)
    body = text[start:end].strip("\n")

    if not body.strip():
        return []

    if "FILE:" not in body:
        raise error_cls("No FILE: headers found inside file bundle.")

    entries: List[Tuple[str, str]] = []
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
        entries.append((relpath, "\n".join(buf).rstrip("\n") + "\n"))

    if not entries:
        raise error_cls("No FILE: blocks could be parsed (check FILE:/END_FILE lines).")

    return entries


def classify_duplicate_file_entries(
    *,
    entries: List[Tuple[str, str]],
    normalize_newlines: Callable[[str], str],
) -> Tuple[Dict[str, str], Dict[str, List[str]], List[str]]:
    grouped: Dict[str, List[str]] = {}
    for relpath, content in entries:
        path = relpath.strip()
        if not path:
            continue
        grouped.setdefault(path, []).append(content)

    normalized: Dict[str, str] = {}
    conflicts: Dict[str, List[str]] = {}
    equivalent_duplicates: List[str] = []

    for relpath, variants in grouped.items():
        canonical_variants = [normalize_newlines(v).rstrip("\n") + "\n" for v in variants]
        first = canonical_variants[0]
        if all(v == first for v in canonical_variants[1:]):
            normalized[relpath] = first
            if len(canonical_variants) > 1:
                equivalent_duplicates.append(relpath)
        else:
            conflicts[relpath] = canonical_variants

    return normalized, conflicts, sorted(equivalent_duplicates)




def classify_bundle_transport_failure(
    *,
    raw_text: str,
    error_message: str,
    expected_paths: List[str] | None = None,
    parsed_paths: List[str] | None = None,
    normalize_newlines: Callable[[str], str] | None = None,
    file_bundle_begin: str = "BEGIN_FILE_BUNDLE",
    file_bundle_end: str = "END_FILE_BUNDLE",
    file_header_re: Pattern[str] | None = None,
) -> Dict[str, Any]:
    normalize = normalize_newlines or (lambda value: str(value or "").replace("\r\n", "\n").replace("\r", "\n"))
    normalized = normalize(raw_text)
    message = str(error_message or "")
    msg_lower = message.lower()
    expected = [str(path).strip().replace("\\", "/") for path in (expected_paths or []) if str(path).strip()]
    parsed = [str(path).strip().replace("\\", "/") for path in (parsed_paths or []) if str(path).strip()]

    has_begin = file_bundle_begin in normalized
    has_end = file_bundle_end in normalized
    markers_present = False
    body = ""
    if has_begin and has_end:
        begin_index = normalized.index(file_bundle_begin) + len(file_bundle_begin)
        end_index = normalized.index(file_bundle_end)
        if begin_index <= end_index:
            markers_present = True
            body = normalized[begin_index:end_index].strip("\n")

    header_re = file_header_re or re.compile(r"^FILE:\s+(.+?)\s*$")
    file_header_count = 0
    if body:
        for line in body.split("\n"):
            if header_re.match(line):
                file_header_count += 1

    missing_paths: List[str] = []
    if "missing file blocks from the requested scope:" in msg_lower:
        suffix = message.split(":", 1)[1] if ":" in message else ""
        missing_paths = [item.strip() for item in suffix.split(",") if item.strip()]
    elif expected and parsed:
        missing_paths = sorted(set(expected) - set(parsed))

    category = "bundle_transport"
    summary = "Generic bundle transport failure."
    structurally_valid = False

    if "missing file blocks from the requested scope:" in msg_lower:
        category = "bundle_underfilled_response"
        summary = "Structurally valid bundle omitted one or more requested FILE blocks."
        structurally_valid = True
    elif ("model output missing begin_file_bundle/end_file_bundle markers." in msg_lower) or (normalized.strip() and not markers_present and (not has_begin or not has_end)):
        category = "bundle_markerless_transport"
        summary = "Response did not include a usable BEGIN_FILE_BUNDLE/END_FILE_BUNDLE transport wrapper."
    elif markers_present and not body.strip():
        category = "bundle_empty_response"
        summary = "Bundle transport was present but contained zero FILE blocks."
    elif any(token in msg_lower for token in (
        "no file: headers found inside file bundle",
        "no file: blocks could be parsed",
        "nested file header encountered before end_file",
        "missing end_file",
        "duplicate file path in bundle",
        "unexpected file blocks outside the requested scope",
        "empty file: path",
    )):
        category = "bundle_malformed_transport"
        summary = "Bundle transport was present but malformed or policy-violating."
    elif "bundle" in msg_lower or "end_file" in msg_lower or "begin_file_bundle" in msg_lower or markers_present:
        category = "bundle_malformed_transport"
        summary = "Bundle transport failure could not be narrowed beyond malformed transport."

    return {
        "failure_category": category,
        "bundle_failure_summary": summary,
        "bundle_markers_present": markers_present,
        "bundle_empty": category == "bundle_empty_response",
        "bundle_underfilled": category == "bundle_underfilled_response",
        "bundle_markerless": category == "bundle_markerless_transport",
        "bundle_malformed": category == "bundle_malformed_transport",
        "bundle_structurally_valid": structurally_valid,
        "expected_paths": expected,
        "parsed_paths": parsed,
        "missing_paths": missing_paths,
        "bundle_file_header_count": file_header_count,
    }

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


def parse_transport_payload(
    *,
    text: str,
    transport: str,
    normalize_newlines: Callable[[str], str],
    file_bundle_begin: str,
    file_bundle_end: str,
    file_header_re: Pattern[str],
    file_end: str,
    error_cls: Type[Exception],
    existing_files: Dict[str, str] | None = None,
) -> Dict[str, str]:
    transport_value = str(transport or "file_bundle").strip().lower() or "file_bundle"
    if transport_value == "patch":
        from agents.lib.patch_apply import materialize_patch_apply_payload

        return materialize_patch_apply_payload(
            text=text,
            existing_files=existing_files or {},
            normalize_newlines=normalize_newlines,
            error_cls=error_cls,
        )

    return parse_file_bundle(
        text=text,
        normalize_newlines=normalize_newlines,
        file_bundle_begin=file_bundle_begin,
        file_bundle_end=file_bundle_end,
        file_header_re=file_header_re,
        file_end=file_end,
        error_cls=error_cls,
    )


def looks_like_alternate_patch_transport(
    *,
    text: str,
    normalize_newlines: Callable[[str], str],
) -> bool:
    from agents.lib.patch_apply import looks_like_patch_apply_payload

    return looks_like_patch_apply_payload(text=text, normalize_newlines=normalize_newlines)
