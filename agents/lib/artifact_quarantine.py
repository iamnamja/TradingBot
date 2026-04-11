from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Iterable, Mapping

KNOWN_SAFE_ARTIFACT_NAMES = (
    "last_output.txt",
    "_last_agent_model_output.txt",
    "_last_agent_file_bundle.txt",
    "_last_agent_file_bundle_error.txt",
    "_last_subset_preservation.json",
)

LEGACY_RUNTIME_ARTIFACT_NAME_ALIASES = {
    "_last_agent_file_bundlee_error.txt": "_last_agent_file_bundle_error.txt",
}


def normalize_runtime_artifact_name(name: str) -> str:
    return str(LEGACY_RUNTIME_ARTIFACT_NAME_ALIASES.get(str(name), str(name)))


def _normalized_names(paths: Iterable[Path]) -> list[str]:
    names: list[str] = []
    seen: set[str] = set()
    for path in paths:
        normalized = normalize_runtime_artifact_name(path.name)
        if normalized in seen:
            continue
        seen.add(normalized)
        names.append(normalized)
    return names


def classify_runtime_artifacts(
    paths: Iterable[Path],
    *,
    known_safe_names: Iterable[str] = KNOWN_SAFE_ARTIFACT_NAMES,
) -> dict[str, list[Path]]:
    safe = {normalize_runtime_artifact_name(str(name)) for name in known_safe_names}
    known_safe: list[Path] = []
    unknown: list[Path] = []

    for path in paths:
        if normalize_runtime_artifact_name(path.name) in safe:
            known_safe.append(path)
        else:
            unknown.append(path)

    return {"known_safe": known_safe, "unknown": unknown}


def quarantine_runtime_artifacts(
    paths: Iterable[Path],
    *,
    run_git_command: Callable[..., object],
    path_exists: Callable[[Path], bool],
    unlink_path: Callable[[Path], None],
    known_safe_names: Iterable[str] = KNOWN_SAFE_ARTIFACT_NAMES,
    retain_known_safe: bool = False,
) -> dict[str, object]:
    classified = classify_runtime_artifacts(paths, known_safe_names=known_safe_names)

    quarantined: list[Path] = []
    retained: list[Path] = []

    for path in classified["known_safe"]:
        try:
            run_git_command(
                ["git", "rm", "--cached", "--quiet", "--ignore-unmatch", path.as_posix()],
                check=False,
            )
        except Exception:
            pass

        if retain_known_safe:
            retained.append(path)
            continue

        try:
            if path_exists(path):
                unlink_path(path)
                quarantined.append(path)
            else:
                quarantined.append(path)
        except Exception:
            pass

    unknown = list(classified["unknown"])
    return {
        "classified": classified,
        "quarantined": quarantined,
        "retained": retained,
        "warnings": {
            "quarantined_known_safe": _normalized_names(classified["known_safe"]),
            "retained_known_safe": _normalized_names(retained),
            "unknown_artifacts": [p.as_posix() for p in unknown],
        },
        "lifecycle": {
            "known_safe_action": "retained" if retain_known_safe else "quarantined_removed",
            "unknown_action": "blocked" if unknown else "none",
        },
        "should_block": bool(unknown),
    }


def describe_runtime_artifact_lifecycle(decision: Mapping[str, Any]) -> list[str]:
    warnings = decision.get("warnings", {})
    lifecycle = decision.get("lifecycle", {})
    if not isinstance(warnings, Mapping):
        warnings = {}
    if not isinstance(lifecycle, Mapping):
        lifecycle = {}

    quarantined = [str(x) for x in warnings.get("quarantined_known_safe", []) or []]
    retained = [str(x) for x in warnings.get("retained_known_safe", []) or []]
    unknown = [str(x) for x in warnings.get("unknown_artifacts", []) or []]

    messages: list[str] = []
    known_safe_action = str(lifecycle.get("known_safe_action", "") or "")
    if retained and known_safe_action == "retained":
        messages.append(
            "ℹ️ Retained known-safe runtime artifacts (unstaged): " + ", ".join(retained)
        )
    elif quarantined and known_safe_action == "quarantined_removed":
        messages.append(
            "ℹ️ Quarantined and removed known-safe runtime artifacts before commit: "
            + ", ".join(quarantined)
        )

    if unknown:
        messages.append(
            "⚠️ Unknown runtime artifacts remain blocked for manual review: "
            + ", ".join(unknown)
        )

    return messages
