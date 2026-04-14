from __future__ import annotations

import re

import pytest

from agents.lib.bundle_parser import parse_file_bundle, parse_transport_payload
from agents.lib.patch_apply import PatchApplyOperation, looks_like_patch_apply_payload, materialize_patch_apply_payload, parse_patch_apply_operations


class TransportParseError(RuntimeError):
    pass


def _normalize(value: str) -> str:
    return str(value or "").replace("\r\n", "\n").replace("\r", "\n")


def _file_header_re() -> re.Pattern[str]:
    return re.compile(r"^FILE:\s+(.+?)\s*$")


def _bundle_text() -> str:
    return (
        "BEGIN_FILE_BUNDLE\n"
        "FILE: a.py\n"
        "x = 1\n"
        "END_FILE\n"
        "FILE: b.txt\n"
        "hello\n"
        "END_FILE\n"
        "END_FILE_BUNDLE\n"
    )


def test_file_bundle_transport_path_remains_unchanged() -> None:
    parsed = parse_transport_payload(
        text=_bundle_text(),
        transport="file_bundle",
        normalize_newlines=_normalize,
        file_bundle_begin="BEGIN_FILE_BUNDLE",
        file_bundle_end="END_FILE_BUNDLE",
        file_header_re=_file_header_re(),
        file_end="END_FILE",
        error_cls=TransportParseError,
    )
    assert parsed == {"a.py": "x = 1\n", "b.txt": "hello\n"}


def test_normalized_patch_apply_payload_parses_and_materializes() -> None:
    text = (
        "BEGIN_PATCH_APPLY\n"
        "ADD_FILE: new.txt\n"
        "BEGIN_CONTENT\n"
        "hello\n"
        "world\n"
        "END_CONTENT\n"
        "UPDATE_FILE: keep.txt\n"
        "BEGIN_CONTENT\n"
        "replaced\n"
        "END_CONTENT\n"
        "DELETE_FILE: old.txt\n"
        "END_PATCH_APPLY\n"
    )
    ops = parse_patch_apply_operations(text=text, normalize_newlines=_normalize, error_cls=TransportParseError)
    assert ops == [
        PatchApplyOperation(kind="add", path="new.txt", content="hello\nworld\n"),
        PatchApplyOperation(kind="update", path="keep.txt", content="replaced\n"),
        PatchApplyOperation(kind="delete", path="old.txt", content=None),
    ]

    files = materialize_patch_apply_payload(
        text=text,
        existing_files={"keep.txt": "old\n", "old.txt": "bye\n"},
        normalize_newlines=_normalize,
        error_cls=TransportParseError,
    )
    assert files == {"keep.txt": "replaced\n", "new.txt": "hello\nworld\n"}


def test_codex_style_apply_patch_fixture_materializes_without_bundle_headers() -> None:
    text = (
        "apply_patch <<'PATCH'\n"
        "*** Begin Patch\n"
        "*** Add File: hello.txt\n"
        "+hello\n"
        "+world\n"
        "*** Update File: keep.txt\n"
        "+rewritten\n"
        "*** Delete File: drop.txt\n"
        "*** End Patch\n"
        "PATCH\n"
    )
    assert looks_like_patch_apply_payload(text=text, normalize_newlines=_normalize) is True

    files = parse_transport_payload(
        text=text,
        transport="patch",
        normalize_newlines=_normalize,
        file_bundle_begin="BEGIN_FILE_BUNDLE",
        file_bundle_end="END_FILE_BUNDLE",
        file_header_re=_file_header_re(),
        file_end="END_FILE",
        error_cls=TransportParseError,
        existing_files={"keep.txt": "before\n", "drop.txt": "remove\n"},
    )
    assert files == {"hello.txt": "hello\nworld\n", "keep.txt": "rewritten\n"}


def test_regression_patch_payload_would_fail_bundle_parser_but_succeeds_with_transport_hint() -> None:
    text = (
        "BEGIN_PATCH_APPLY\n"
        "ADD_FILE: sample.txt\n"
        "BEGIN_CONTENT\n"
        "value\n"
        "END_CONTENT\n"
        "END_PATCH_APPLY\n"
    )
    with pytest.raises(TransportParseError):
        parse_file_bundle(
            text=text,
            normalize_newlines=_normalize,
            file_bundle_begin="BEGIN_FILE_BUNDLE",
            file_bundle_end="END_FILE_BUNDLE",
            file_header_re=_file_header_re(),
            file_end="END_FILE",
            error_cls=TransportParseError,
        )

    files = parse_transport_payload(
        text=text,
        transport="patch",
        normalize_newlines=_normalize,
        file_bundle_begin="BEGIN_FILE_BUNDLE",
        file_bundle_end="END_FILE_BUNDLE",
        file_header_re=_file_header_re(),
        file_end="END_FILE",
        error_cls=TransportParseError,
    )
    assert files == {"sample.txt": "value\n"}
