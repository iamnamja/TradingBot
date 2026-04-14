from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import json


@dataclass(frozen=True)
class AdjacentPair:
    pair_id: str
    task_a: str
    task_b: str
    relation: str
    eligible: bool
    supervision: Optional[str] = None
    notes: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class PairCorpus:
    pairs: List[AdjacentPair]

    def eligible_pairs(self) -> List[AdjacentPair]:
        return [p for p in self.pairs if p.eligible]

    def ineligible_pairs(self) -> List[AdjacentPair]:
        return [p for p in self.pairs if not p.eligible]

    def by_id(self) -> Dict[str, AdjacentPair]:
        return {p.pair_id: p for p in self.pairs}

    def as_task_pairs(self) -> List[Tuple[str, str]]:
        return [(p.task_a, p.task_b) for p in self.eligible_pairs()]


# Compatibility alias to satisfy potential external references
PairManifest = PairCorpus


def _normalize_entry(raw: Dict[str, Any]) -> AdjacentPair:
    # Aliases for schema normalization
    pair_id = (
        raw.get("pair_id")
        or raw.get("id")
        or raw.get("pairId")
        or raw.get("pair")
    )
    task_a = raw.get("task_a") or raw.get("a") or raw.get("taskA") or raw.get("task_a_path")
    task_b = raw.get("task_b") or raw.get("b") or raw.get("taskB") or raw.get("task_b_path")

    relation = (
        raw.get("relation")
        or raw.get("expected_relationship")
        or raw.get("handoff")
        or raw.get("handoff_relation")
        or raw.get("adjacency")
        or "unspecified"
    )

    eligible = (
        raw.get("eligible")
        if "eligible" in raw
        else (
            raw.get("benchmark_eligible")
            if "benchmark_eligible" in raw
            else raw.get("is_eligible", False)
        )
    )
    eligible = bool(eligible)

    supervision = raw.get("supervision") or raw.get("profile") or raw.get("supervision_profile")
    notes = raw.get("notes") or raw.get("comment")

    # Preserve any extra keys as meta
    known_keys = {
        "pair_id",
        "id",
        "pairId",
        "pair",
        "task_a",
        "taskA",
        "a",
        "task_a_path",
        "task_b",
        "taskB",
        "b",
        "task_b_path",
        "relation",
        "expected_relationship",
        "handoff",
        "handoff_relation",
        "adjacency",
        "eligible",
        "benchmark_eligible",
        "is_eligible",
        "supervision",
        "profile",
        "supervision_profile",
        "notes",
        "comment",
    }
    meta = {k: v for k, v in raw.items() if k not in known_keys}

    if not pair_id:
        # Derive a stable id when omitted
        base = f"{task_a or 'UNKNOWN'}->{task_b or 'UNKNOWN'}"
        pair_id = f"{relation}:{base}"

    if not task_a or not task_b:
        # Keep record but ensure values are strings for durability
        task_a = task_a or "UNKNOWN"
        task_b = task_b or "UNKNOWN"

    return AdjacentPair(
        pair_id=str(pair_id),
        task_a=str(task_a),
        task_b=str(task_b),
        relation=str(relation),
        eligible=eligible,
        supervision=str(supervision) if supervision is not None else None,
        notes=str(notes) if notes is not None else None,
        meta=meta,
    )


def _parse_pairs_payload(payload: Any) -> List[AdjacentPair]:
    if isinstance(payload, dict):
        # accept either a root "pairs" array or a mapping of id->entry
        if "pairs" in payload and isinstance(payload["pairs"], list):
            entries = payload["pairs"]
        else:
            # treat dict values as entries
            entries = list(payload.values())
    elif isinstance(payload, list):
        entries = payload
    else:
        entries = []

    normalized: List[AdjacentPair] = []
    for item in entries:
        if not isinstance(item, dict):
            continue
        normalized.append(_normalize_entry(item))
    return normalized


def load_pair_manifest(path: Union[str, Path]) -> PairCorpus:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    pairs = _parse_pairs_payload(data)
    return PairCorpus(pairs=pairs)


# Compatibility shims for broader test surface
def parse_bounded_two_task_pairs_manifest(path: Union[str, Path]) -> PairManifest:
    return load_pair_manifest(path)


def load_bounded_two_task_pairs(path: Union[str, Path]) -> PairManifest:
    return load_pair_manifest(path)


def bounded_two_task_candidates_from_manifest(path: Union[str, Path]) -> List[Tuple[str, str]]:
    manifest = load_pair_manifest(path)
    return manifest.as_task_pairs()


__all__ = [
    "AdjacentPair",
    "PairCorpus",
    "PairManifest",
    "load_pair_manifest",
    "parse_bounded_two_task_pairs_manifest",
    "load_bounded_two_task_pairs",
    "bounded_two_task_candidates_from_manifest",
]
