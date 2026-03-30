from __future__ import annotations

from typing import Iterable, Tuple


# Canonical meta harness paths that are always handled via protected method mode
DEFAULT_PROTECTED_META_PATHS: tuple[str, ...] = (
    "agents/run_task.py",
    "agents/lib/shell_router.py",
    "agents/lib/bundle_parser.py",
    "agents/lib/protected_file_policy.py",
)


def _normalize_paths(paths: Iterable[str] | None) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for raw in paths or []:
        if not isinstance(raw, str):
            continue
        p = raw.strip().replace("\\", "/")
        if not p or p in seen:
            continue
        seen.add(p)
        out.append(p)
    return out


def _explicit_protected_from_targets(protected_targets: Iterable[dict] | Iterable[str] | None) -> set[str]:
    out: set[str] = set()
    for target in protected_targets or []:
        if isinstance(target, dict):
            p = target.get("path")
            if isinstance(p, str) and p.strip():
                out.add(p.strip().replace("\\", "/"))
        elif isinstance(target, str) and target.strip():
            out.add(target.strip().replace("\\", "/"))
    return out


def partition_required_paths_for_normal_bundle(
    required_paths: Iterable[str],
    protected_targets: Iterable[dict] | Iterable[str] | None = None,
    protected_meta_paths: Iterable[str] | None = None,
    protected_meta_harness_paths: Iterable[str] | None = None,
) -> Tuple[list[str], list[str]]:
    """
    Partition required deliverable paths into:
    - normal bundle paths (returned first)
    - protected paths (returned second), which must be edited via protected method mode.

    Inputs:
    - required_paths: all deliverables from the task text
    - protected_targets: explicit protected-method edit targets (dicts with 'path') or raw strings
    - protected_meta_paths / protected_meta_harness_paths: optional override for canonical protected meta files

    Behavior:
    - Preserves original order from required_paths
    - De-duplicates within each partition
    - Treats any path in the meta harness set or explicit targets as protected
    """
    # Support both parameter spellings (shell_router/run_task use slightly different kw names).
    meta_iter = protected_meta_harness_paths if protected_meta_harness_paths is not None else protected_meta_paths
    meta_set = {p.strip().replace("\\", "/") for p in (meta_iter or DEFAULT_PROTECTED_META_PATHS) if isinstance(p, str) and p.strip()}
    explicit_protected = _explicit_protected_from_targets(protected_targets)

    normal: list[str] = []
    protected: list[str] = []
    seen_normal: set[str] = set()
    seen_protected: set[str] = set()

    for raw in _normalize_paths(required_paths):
        is_protected = (raw in meta_set) or (raw in explicit_protected)
        if is_protected:
            if raw not in seen_protected:
                protected.append(raw)
                seen_protected.add(raw)
        else:
            if raw not in seen_normal:
                normal.append(raw)
                seen_normal.add(raw)

    # Ensure every explicit/meta-protected path is present in the protected list,
    # even if not listed in required_paths (order does not matter in this edge case).
    for extra in sorted(explicit_protected | meta_set):
        if extra not in seen_protected and extra in (_normalize_paths(required_paths)):
            protected.append(extra)
            seen_protected.add(extra)

    # Remove any accidental overlap from normal (shouldn't happen with the logic above)
    if seen_protected:
        normal = [p for p in normal if p not in seen_protected]

    return normal, protected
