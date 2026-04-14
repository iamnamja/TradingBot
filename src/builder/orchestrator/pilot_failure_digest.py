from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


# Canonical bounded two-task pilot failure kinds
PILOT_FAILURE_KINDS = {
    "admission_blocked",
    "handoff_incomplete",
    "handoff_incompatible",
    "controller_override",
    "manual_stop",
    "runtime_failure",
}


@dataclass
class SupervisionEvent:
    # Minimal durable supervision truth for bounded pilot runs
    session_id: str
    pair_id: str
    phase: str  # e.g., "admission", "builder", "handoff", "verifier", "controller"
    reason: str
    invalidates_autonomy: bool
    pilot_completed: bool
    meta: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "session_id": self.session_id,
            "pair_id": self.pair_id,
            "phase": self.phase,
            "reason": self.reason,
            "invalidates_autonomy": self.invalidates_autonomy,
            "pilot_completed": self.pilot_completed,
            "meta": self.meta or {},
        }

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "SupervisionEvent":
        return SupervisionEvent(
            session_id=str(data.get("session_id", "")),
            pair_id=str(data.get("pair_id", "")),
            phase=str(data.get("phase", "")),
            reason=str(data.get("reason", "")),
            invalidates_autonomy=bool(data.get("invalidates_autonomy", False)),
            pilot_completed=bool(data.get("pilot_completed", False)),
            meta=dict(data.get("meta", {}) or {}),
        )


@dataclass
class SupervisionLedger:
    # Durable, append-only supervision ledger
    path: Path
    events: List[SupervisionEvent] = field(default_factory=list)

    def record_event(
        self,
        session_id: str,
        pair_id: str,
        phase: str,
        reason: str,
        invalidates_autonomy: bool,
        pilot_completed: bool,
        meta: Optional[Dict[str, str]] = None,
    ) -> SupervisionEvent:
        evt = SupervisionEvent(
            session_id=session_id,
            pair_id=pair_id,
            phase=phase,
            reason=reason,
            invalidates_autonomy=invalidates_autonomy,
            pilot_completed=pilot_completed,
            meta=meta or {},
        )
        self.events.append(evt)
        self.save()
        return evt

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [e.to_dict() for e in self.events]
        self.path.write_text(json.dumps(data, indent=2, sort_keys=True))

    @classmethod
    def load(cls, path: Path) -> "SupervisionLedger":
        if not path.exists():
            return cls(path=path, events=[])
        try:
            raw = json.loads(path.read_text() or "[]")
        except Exception:
            # If corrupted, keep safe empty to never block runs
            raw = []
        events = [SupervisionEvent.from_dict(x) for x in raw if isinstance(x, dict)]
        return cls(path=path, events=events)


@dataclass
class PilotFailureDigestEntry:
    pair_id: str
    kind: str
    detail: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        return {
            "pair_id": self.pair_id,
            "kind": self.kind,
            "detail": self.detail,
        }

    @staticmethod
    def from_dict(data: Dict[str, object]) -> "PilotFailureDigestEntry":
        return PilotFailureDigestEntry(
            pair_id=str(data.get("pair_id", "")),
            kind=str(data.get("kind", "")),
            detail=(None if data.get("detail") is None else str(data.get("detail"))),
        )


@dataclass
class PilotFailureDigest:
    # Bounded pilot failure digest for two-task pilot runs
    path: Path
    entries: List[PilotFailureDigestEntry] = field(default_factory=list)
    counts: Dict[str, int] = field(default_factory=dict)

    def record(self, kind: str, pair_id: str, detail: Optional[str] = None) -> PilotFailureDigestEntry:
        if kind not in PILOT_FAILURE_KINDS:
            # Normalize any unexpected kind into runtime_failure to keep digest compatible
            detail = f"{kind}: {detail}" if detail else kind
            kind = "runtime_failure"
        entry = PilotFailureDigestEntry(pair_id=pair_id, kind=kind, detail=detail)
        self.entries.append(entry)
        self.counts[kind] = self.counts.get(kind, 0) + 1
        self.save()
        return entry

    def summary(self) -> Dict[str, int]:
        # Return a stable, deterministic summary of counts across known buckets
        out: Dict[str, int] = {}
        for k in sorted(PILOT_FAILURE_KINDS):
            out[k] = self.counts.get(k, 0)
        return out

    def to_dict(self) -> Dict[str, object]:
        return {
            "entries": [e.to_dict() for e in self.entries],
            "counts": dict(self.counts),
        }

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.to_dict(), indent=2, sort_keys=True))

    @classmethod
    def load(cls, path: Path) -> "PilotFailureDigest":
        if not path.exists():
            return cls(path=path, entries=[], counts={})
        try:
            raw = json.loads(path.read_text() or "{}")
        except Exception:
            raw = {}
        raw_entries = raw.get("entries", []) or []
        entries = [PilotFailureDigestEntry.from_dict(e) for e in raw_entries if isinstance(e, dict)]
        counts_in = raw.get("counts", {}) or {}
        counts: Dict[str, int] = {}
        if isinstance(counts_in, dict):
            for k, v in counts_in.items():
                try:
                    counts[str(k)] = int(v)
                except Exception:
                    continue
        # Ensure keys exist for known buckets for stability
        for k in PILOT_FAILURE_KINDS:
            counts.setdefault(k, 0)
        return cls(path=path, entries=entries, counts=counts)


__all__ = [
    "PILOT_FAILURE_KINDS",
    "SupervisionEvent",
    "SupervisionLedger",
    "PilotFailureDigestEntry",
    "PilotFailureDigest",
]
