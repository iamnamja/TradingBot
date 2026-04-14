import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


COMPLETED_THROUGH_PATTERNS: List[re.Pattern[str]] = [
    # README.md style: "complete through Task 185"
    re.compile(r"complete through Task\s+(\d{1,4})", re.IGNORECASE),
    # State doc style: "post-Task 185"
    re.compile(r"post-Task\s+(\d{1,4})", re.IGNORECASE),
]

# Match "186–190" (en-dash) or "186-190" (hyphen), anywhere in the text.
ACTIVE_TRANCHE_RANGE_PATTERN: re.Pattern[str] = re.compile(
    r"\b(\d{3,4})\s*[\u2013-]\s*(\d{3,4})\b"
)


def extract_completed_through_task(text: str) -> Optional[int]:
    # Try patterns in order; return the first found.
    for pat in COMPLETED_THROUGH_PATTERNS:
        m = pat.search(text)
        if m:
            try:
                return int(m.group(1))
            except ValueError:
                continue
    return None


def _normalize_tranche_tuple(value: Tuple[int, int]) -> Tuple[int, int]:
    a, b = value
    # Ensure start <= end
    return (a, b) if a <= b else (b, a)


def extract_active_tranche(text: str) -> Optional[Tuple[int, int]]:
    # Collect all ranges; return the range with the highest end (deterministic tie-breaker on start).
    candidates: List[Tuple[int, int]] = []
    for m in ACTIVE_TRANCHE_RANGE_PATTERN.finditer(text):
        try:
            a = int(m.group(1))
            b = int(m.group(2))
        except ValueError:
            continue
        candidates.append(_normalize_tranche_tuple((a, b)))
    if not candidates:
        return None
    # Prefer the range with the largest end; tie-break on largest start for determinism.
    candidates.sort(key=lambda ab: (ab[1], ab[0]))
    return candidates[-1]


def _mode_value(values: List[object]) -> Optional[object]:
    if not values:
        return None
    counts: Dict[object, int] = {}
    for v in values:
        counts[v] = counts.get(v, 0) + 1
    # Deterministic selection: sort by (-count, value as tuple for stable ordering)
    # Convert values to a comparable key; tuples/ints are comparable among themselves in Python.
    # Mixed types will be stringified for comparison.
    def sort_key(item: Tuple[object, int]) -> Tuple[int, str]:
        v, c = item
        return (-c, repr(v))

    return sorted(counts.items(), key=sort_key)[0][0]


def _tranche_str(value: Optional[Tuple[int, int]]) -> Optional[str]:
    if value is None:
        return None
    return f"{value[0]}-{value[1]}"


def build_report(paths: Iterable[Path]) -> Dict[str, object]:
    # Read files and extract values.
    completed_by_file: Dict[str, Optional[int]] = {}
    tranche_by_file: Dict[str, Optional[Tuple[int, int]]] = {}

    for p in paths:
        try:
            text = Path(p).read_text(encoding="utf-8")
        except FileNotFoundError:
            text = ""
        completed_by_file[str(p)] = extract_completed_through_task(text)
        tranche_by_file[str(p)] = extract_active_tranche(text)

    # Compute consensus (mode) values across available (non-None) values.
    completed_values = [v for v in completed_by_file.values() if v is not None]
    tranche_values = [v for v in tranche_by_file.values() if v is not None]

    completed_consensus: Optional[int] = _mode_value(completed_values)  # type: ignore[assignment]
    tranche_consensus: Optional[Tuple[int, int]] = _mode_value(tranche_values)  # type: ignore[assignment]

    # Compute disagreements: any file with a present value not equal to the consensus.
    completed_disagreements: List[str] = []
    tranche_disagreements: List[str] = []

    for fpath, val in completed_by_file.items():
        if val is not None and completed_consensus is not None and val != completed_consensus:
            completed_disagreements.append(fpath)

    for fpath, val in tranche_by_file.items():
        if val is not None and tranche_consensus is not None and val != tranche_consensus:
            tranche_disagreements.append(fpath)

    report: Dict[str, object] = {
        "completed_through": {
            "consensus": completed_consensus,
            "by_file": completed_by_file,
            "disagreements": completed_disagreements,
        },
        "active_tranche": {
            "consensus": _tranche_str(tranche_consensus),
            "by_file": {k: _tranche_str(v) for k, v in tranche_by_file.items()},
            "disagreements": tranche_disagreements,
        },
    }
    return report


def validate_docs_status(paths: Iterable[Path]) -> Tuple[bool, Dict[str, object]]:
    report = build_report(paths)
    completed_disagreements: List[str] = report["completed_through"]["disagreements"]  # type: ignore[assignment]
    tranche_disagreements: List[str] = report["active_tranche"]["disagreements"]  # type: ignore[assignment]
    ok = len(completed_disagreements) == 0 and len(tranche_disagreements) == 0
    return ok, report


def default_guard_paths() -> List[Path]:
    return [
        Path("README.md"),
        Path("docs/README.md"),
        Path("docs/TRADINGBOT_PROJECT_STATE.md"),
    ]


def _json_dump(report: Dict[str, object]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)


def main() -> int:
    paths = default_guard_paths()
    ok, report = validate_docs_status(paths)
    print(_json_dump(report))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
