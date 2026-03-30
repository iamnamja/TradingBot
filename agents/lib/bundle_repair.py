from __future__ import annotations

from typing import Callable, Dict, List, Tuple


def classify_duplicate_file_entries(
    entries: List[Tuple[str, str]],
    normalize_newlines: Callable[[str], str] | None = None,
) -> Tuple[Dict[str, str], Dict[str, List[str]], List[str]]:
    """
    Classify duplicate FILE entries into:
    - normalized: a dict[path] = single canonical content when all duplicates are byte-equivalent
    - conflicts: a dict[path] = list of canonical variants when content differs
    - equivalent: a sorted list of paths that had duplicates but were byte-equivalent

    This mirrors the controller-side behavior so both run_task and shell_router can keep parity
    while delegating the duplicate/conflict logic to a shared helper.
    """
    normalizer = normalize_newlines or (lambda s: s)

    grouped: Dict[str, List[str]] = {}
    for relpath, content in entries:
        path = (relpath or "").strip().replace("\\", "/")
        if not path:
            continue
        grouped.setdefault(path, []).append(content)

    normalized: Dict[str, str] = {}
    conflicts: Dict[str, List[str]] = {}
    equivalent: List[str] = []

    for relpath, variants in grouped.items():
        # Normalize newline variants deterministically to compare canonical content.
        canonical = [normalizer(v).rstrip("\n") + "\n" for v in variants]
        first = canonical[0]
        if all(v == first for v in canonical[1:]):
            normalized[relpath] = first
            if len(canonical) > 1:
                equivalent.append(relpath)
        else:
            conflicts[relpath] = canonical

    equivalent.sort()
    return normalized, conflicts, equivalent
