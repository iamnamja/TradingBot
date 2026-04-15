from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _write_json(path: Path, data: dict) -> None:
    _ensure_dir(path.parent)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)


@dataclass
class Scorecard:
    total_runs: int = 0
    direct_completions: int = 0
    self_healed_completions: int = 0
    failed_runs: int = 0
    authority_blocked_runs: int = 0
    supervised_runs: int = 0
    invalidated_by_human_intervention: int = 0

    def successes(self) -> int:
        return self.direct_completions + self.self_healed_completions

    def failures(self) -> int:
        # Failures are everything that is not counted as an autonomous success.
        return max(self.total_runs - self.successes(), 0)

    def pass_rate(self) -> float:
        return self.successes() / self.total_runs if self.total_runs else 0.0

    def to_dict(self) -> dict:
        data = asdict(self)
        data["successes"] = self.successes()
        data["failures"] = self.failures()
        data["pass_rate"] = round(self.pass_rate(), 4) if self.total_runs else 0.0
        return data

    def _rates(self) -> Dict[str, float]:
        total = self.total_runs or 1  # avoid div-by-zero
        return {
            "pass_rate": self.pass_rate(),
            "direct_rate": self.direct_completions / total,
            "self_healed_rate": self.self_healed_completions / total,
            "supervised_rate": self.supervised_runs / total,
            "authority_ambiguity_rate": self.authority_blocked_runs / total,
            "invalidated_rate": self.invalidated_by_human_intervention / total,
        }


@dataclass(frozen=True)
class PromotionThresholds:
    # Minimum autonomous completion rate across the curated set
    min_pass_rate: float = 0.6
    # "Materially better" margin for direct vs self-healed completions
    min_direct_minus_self_healed_margin: float = 0.2
    # Supervision/escalation rate must remain low
    max_supervised_rate: float = 0.1
    # Unresolved authority-ambiguity must remain very low
    max_authority_ambiguity_rate: float = 0.05
    # No recurring compatibility seam regressions allowed in the benchmark set
    require_no_compat_regressions: bool = True


@dataclass(frozen=True)
class EmptyOutputGuard:
    """Small regression guard configuration for empty-output failures."""
    max_empty_output_rate: float = 0.10


class BenchmarkSession:
    """
    Integrated scorecard writer for benchmark sessions.

    This session integrates a strict no-manual-intervention scorecard directly into the
    benchmark session artifact directory. It preserves the existing pass-rate scoreboard
    surface while adding a durable scorecard.json with full, strict counts.

    It also produces a promotion.json artifact with an explicit verdict and thresholds.
    """

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.scorecard = Scorecard()
        self.thresholds = PromotionThresholds()
        self.empty_output_guard = EmptyOutputGuard()

    def record_run(
        self,
        *,
        direct_completion: bool = False,
        self_healed_completion: bool = False,
        failed: bool = False,
        authority_blocked: bool = False,
        supervised: bool = False,
        manual_edit: bool = False,
    ) -> None:
        """
        Record a single benchmark run result into the session.

        Strict no-manual-intervention rule:
        - If manual_edit is True, the run is not counted as an autonomous success,
          even if it otherwise looks like a direct or self-healed completion.
        - The run is tracked under 'invalidated_by_human_intervention' and treated as
          a failure for the pass-rate scoreboard surface.
        """
        self.scorecard.total_runs += 1

        if manual_edit:
            self.scorecard.invalidated_by_human_intervention += 1
            # If caller didn't specify another explicit non-success bucket, count it as failure.
            if not (failed or authority_blocked or supervised):
                self.scorecard.failed_runs += 1
            return

        if authority_blocked:
            self.scorecard.authority_blocked_runs += 1
            return

        if supervised:
            self.scorecard.supervised_runs += 1
            return

        if direct_completion:
            self.scorecard.direct_completions += 1
            return

        if self_healed_completion:
            self.scorecard.self_healed_completions += 1
            return

        # Default fallthrough: failed run (unknown or explicit failure)
        if failed:
            self.scorecard.failed_runs += 1
        else:
            # Treat unknown outcome as failure for conservative pass-rate compatibility
            self.scorecard.failed_runs += 1

    def _build_scoreboard(self) -> dict:
        # Legacy external-safe scoreboard parity with a few richer fields
        return {
            "total": self.scorecard.total_runs,
            "successes": self.scorecard.successes(),
            "failures": self.scorecard.failures(),
            "pass_rate": round(self.scorecard.pass_rate(), 4) if self.scorecard.total_runs else 0.0,
            "direct_completions": self.scorecard.direct_completions,
            "self_healed_completions": self.scorecard.self_healed_completions,
            "generated_at": _utc_now_iso(),
        }

    def _compute_verdict(self) -> str:
        rates = self.scorecard._rates()
        pr = rates["pass_rate"]
        direct_minus_self = rates["direct_rate"] - rates["self_healed_rate"]

        if self.scorecard.total_runs == 0:
            return "not_ready"

        if pr < self.thresholds.min_pass_rate:
            return "not_ready"

        if (
            direct_minus_self >= self.thresholds.min_direct_minus_self_healed_margin
            and rates["supervised_rate"] <= self.thresholds.max_supervised_rate
            and rates["authority_ambiguity_rate"] <= self.thresholds.max_authority_ambiguity_rate
        ):
            return "ready_to_be_default"

        return "conditionally_ready_under_supervision"

    def _build_promotion(self) -> dict:
        rates = self.scorecard._rates()
        verdict = self._compute_verdict()

        thresholds = {
            "min_pass_rate": self.thresholds.min_pass_rate,
            "min_direct_minus_self_healed_margin": self.thresholds.min_direct_minus_self_healed_margin,
            "max_supervised_rate": self.thresholds.max_supervised_rate,
            "max_authority_ambiguity_rate": self.thresholds.max_authority_ambiguity_rate,
            "require_no_compat_regressions": self.thresholds.require_no_compat_regressions,
            "empty_output_guard": {"max_empty_output_rate": self.empty_output_guard.max_empty_output_rate},
        }

        # Surface explicit transport-stable vs supervision-assisted distinction
        transport_stable_direct = self.scorecard.direct_completions
        supervision_assisted_progress = self.scorecard.self_healed_completions + self.scorecard.supervised_runs

        metrics = {
            "total_runs": self.scorecard.total_runs,
            "successes": self.scorecard.successes(),
            "failures": self.scorecard.failures(),
            "pass_rate": round(rates["pass_rate"], 4),
            "direct_completions": self.scorecard.direct_completions,
            "self_healed_completions": self.scorecard.self_healed_completions,
            "supervised_runs": self.scorecard.supervised_runs,
            "authority_blocked_runs": self.scorecard.authority_blocked_runs,
            "invalidated_by_human_intervention": self.scorecard.invalidated_by_human_intervention,
            "direct_rate": round(rates["direct_rate"], 4),
            "self_healed_rate": round(rates["self_healed_rate"], 4),
            "supervised_rate": round(rates["supervised_rate"], 4),
            "authority_ambiguity_rate": round(rates["authority_ambiguity_rate"], 4),
            "invalidated_rate": round(rates["invalidated_rate"], 4),
            "transport_stable_direct_completions": transport_stable_direct,
            "supervision_assisted_progress": supervision_assisted_progress,
        }

        return {
            "verdict": verdict,
            "thresholds": thresholds,
            "metrics": metrics,
            "generated_at": _utc_now_iso(),
        }

    def write_artifacts(self) -> None:
        scorecard_path = self.session_dir / "scorecard.json"
        scoreboard_path = self.session_dir / "scoreboard.json"
        promotion_path = self.session_dir / "promotion.json"

        _write_json(scorecard_path, self.scorecard.to_dict())
        _write_json(scoreboard_path, self._build_scoreboard())
        _write_json(promotion_path, self._build_promotion())

    # Compatibility alias expected by callers
    def close(self) -> None:
        self.write_artifacts()
