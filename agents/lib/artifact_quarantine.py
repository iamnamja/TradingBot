from __future__ import annotations

from pathlib import Path
from typing import Callable, Iterable

KNOWN_SAFE_ARTIFACT_NAMES = (
    "last_output.txt",
    "_last_agent_model_output.txt",
    "_last_agent_file_bundle.txt",
)


def classify_runtime_artifacts(
    paths: Iterable[Path],
    *,
    known_safe_names: Iterable[str] = KNOWN_SAFE_ARTIFACT_NAMES,
) -> dict[str, list[Path]]:
    safe = {str(name) for name in known_safe_names}
    known_safe: list[Path] = []
    unknown: list[Path] = []

    for path in paths:
        if path.name in safe:
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
            "quarantined_known_safe": [p.as_posix() for p in classified["known_safe"]],
            "retained_known_safe": [p.as_posix() for p in retained],
            "unknown_artifacts": [p.as_posix() for p in unknown],
        },
        "lifecycle": {
            "known_safe_action": "retained" if retain_known_safe else "quarantined_removed",
            "unknown_action": "blocked" if unknown else "none",
        },
        "should_block": bool(unknown),
    }
