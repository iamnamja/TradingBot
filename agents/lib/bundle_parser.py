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
