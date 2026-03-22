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
) -> dict[str, object]:
    classified = classify_runtime_artifacts(paths, known_safe_names=known_safe_names)

    quarantined: list[Path] = []
    for path in classified["known_safe"]:
        try:
            run_git_command(
                ["git", "rm", "--cached", "--quiet", "--ignore-unmatch", path.as_posix()],
                check=False,
            )
        except Exception:
            pass
        try:
            if path_exists(path):
                unlink_path(path)
                quarantined.append(path)
        except Exception:
            pass

    unknown = list(classified["unknown"])
    return {
        "classified": classified,
        "quarantined": quarantined,
        "warnings": {
            "quarantined_known_safe": [p.as_posix() for p in classified["known_safe"]],
            "unknown_artifacts": [p.as_posix() for p in unknown],
        },
        "should_block": bool(unknown),
    }
