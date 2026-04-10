from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Literal, Optional, Tuple

RunOutcome = Literal[
    "direct_completion",
    "self_healed_completion",
    "failed",
    "supervised",
    "authority_blocked",
]


@dataclass
class RunRecord:
    run_id: str
    outcome: Optional[RunOutcome] = None
    manual_intervention: bool = False

    def to_tuple(self) -> Tuple[Optional[RunOutcome], bool]:
        return self.outcome, self.manual_intervention


@dataclass
class StrictScorecard:
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: float = field(default_factory=lambda: time.time())
    runs: Dict[str, RunRecord] = field(default_factory=dict)

    def record_run(self, run_id: str, outcome: RunOutcome, manual_intervention: bool = False) -> None:
        rec = self.runs.get(run_id)
        if rec is None:
            self.runs[run_id] = RunRecord(run_id=run_id, outcome=outcome, manual_intervention=manual_intervention)
        else:
            rec.outcome = outcome
            rec.manual_intervention = rec.manual_intervention or manual_intervention

    def mark_manual_intervention(self, run_id: str) -> None:
        rec = self.runs.get(run_id)
        if rec is None:
            self.runs[run_id] = RunRecord(run_id=run_id, outcome=None, manual_intervention=True)
        else:
            rec.manual_intervention = True

    # Aggregates
    def total_runs(self) -> int:
        return len(self.runs)

    def _count_by_outcome(self, outcome: RunOutcome) -> int:
        return sum(1 for r in self.runs.values() if r.outcome == outcome)

    def direct_completions(self) -> int:
        return self._count_by_outcome("direct_completion")

    def self_healed_completions(self) -> int:
        return self._count_by_outcome("self_healed_completion")

    def failed_runs(self) -> int:
        return self._count_by_outcome("failed")

    def supervised_runs(self) -> int:
        return self._count_by_outcome("supervised")

    def authority_blocked_runs(self) -> int:
        return self._count_by_outcome("authority_blocked")

    def invalidated_by_human(self) -> int:
        return sum(1 for r in self.runs.values() if r.manual_intervention)

    def strict_autonomous_successes(self) -> int:
        return sum(
            1
            for r in self.runs.values()
            if (r.outcome in ("direct_completion", "self_healed_completion")) and not r.manual_intervention
        )

    # Legacy compatibility and new strict metrics
    def legacy_autonomous_successes(self) -> int:
        # Legacy pass-rate counts all completions regardless of manual intervention
        return self.direct_completions() + self.self_healed_completions()

    def pass_rate(self) -> float:
        # Legacy pass-rate
        total = self.total_runs()
        return (self.legacy_autonomous_successes() / total) if total else 0.0

    def pass_rate_strict(self) -> float:
        total = self.total_runs()
        return (self.strict_autonomous_successes() / total) if total else 0.0

    def to_dict(self, include_legacy_fields: bool = True) -> dict:
        dct = {
            "session": {
                "id": self.session_id,
                "created_at_epoch": self.created_at,
            },
            "totals": {
                "total_runs": self.total_runs(),
                "direct_completions": self.direct_completions(),
                "self_healed_completions": self.self_healed_completions(),
                "failed_runs": self.failed_runs(),
                "supervised_runs": self.supervised_runs(),
                "authority_blocked_runs": self.authority_blocked_runs(),
                "invalidated_by_human": self.invalidated_by_human(),
            },
            "strict": {
                "autonomous_successes": self.strict_autonomous_successes(),
                "pass_rate": self.pass_rate_strict(),
            },
        }
        if include_legacy_fields:
            # Preserve compatibility for existing pass-rate scoreboard and surfaces
            dct["legacy"] = {
                "autonomous_successes": self.legacy_autonomous_successes(),
                "pass_rate": self.pass_rate(),
            }
            # Top-level aliases for drop-in compatibility where a flat "pass_rate" is expected
            dct["pass_rate"] = dct["legacy"]["pass_rate"]
        return dct

    def save(self, file_path: str, include_legacy_fields: bool = True) -> None:
        payload = self.to_dict(include_legacy_fields=include_legacy_fields)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, sort_keys=True, indent=2)

    @classmethod
    def load(cls, file_path: str) -> StrictScorecard:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        session = data.get("session", {})
        scorecard = cls(
            session_id=session.get("id", str(uuid.uuid4())),
            created_at=session.get("created_at_epoch", time.time()),
        )

        # Reconstruct runs from "totals" is lossy; attempt to reconstruct from a stored runs list if present
        runs_list = data.get("runs")
        if isinstance(runs_list, list):
            for r in runs_list:
                rid = str(r.get("run_id"))
                outcome = r.get("outcome")
                manual = bool(r.get("manual_intervention", False))
                if outcome is not None:
                    scorecard.record_run(rid, outcome, manual_intervention=manual)
                else:
                    scorecard.mark_manual_intervention(rid)

        return scorecard
