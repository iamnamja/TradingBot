from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Union


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
        data["pass_rate"] = round(self.pass_rate(), 4)
        return data


class BenchmarkSession:
    """
    Integrated scorecard writer for benchmark sessions.

    This session integrates a strict no-manual-intervention scorecard directly into the
    benchmark session artifact directory. It preserves the existing pass-rate scoreboard
    surface while adding a durable scorecard.json with full, strict counts.
    """

    def __init__(self, session_dir: Path):
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.scorecard = Scorecard()

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
            # If it doesn't already fall into another explicit non-success bucket,
            # count it as a failed run for scoreboard parity.
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

        # Default fallthrough: failed run
        if failed or True:
            self.scorecard.failed_runs += 1

    def write_artifacts(self) -> None:
        """
        Persist both the integrated strict scorecard and the legacy-compatible scoreboard.

        - scorecard.json: durable strict scorecard with full counts.
        - scoreboard.json: preserved pass-rate surface used by prior tasks.
        """
        scorecard_path = self.session_dir / "scorecard.json"
        with scorecard_path.open("w", encoding="utf-8") as f:
            json.dump(self.scorecard.to_dict(), f, indent=2, sort_keys=True)

        scoreboard = {
            "total": self.scorecard.total_runs,
            "successes": self.scorecard.successes(),
            "failures": self.scorecard.failures(),
            "pass_rate": round(self.scorecard.pass_rate(), 4),
            # Compatibility extensions for richer dashboards:
            "direct_completions": self.scorecard.direct_completions,
            "self_healed_completions": self.scorecard.self_healed_completions,
        }
        with (self.session_dir / "scoreboard.json").open("w", encoding="utf-8") as f:
            json.dump(scoreboard, f, indent=2, sort_keys=True)

    def close(self) -> None:
        self.write_artifacts()


def open_session(session_dir: Union[str, Path]) -> BenchmarkSession:
    """
    Open a benchmark session bound to the given artifact directory.

    The returned session writes its integrated scorecard into the provided path.
    """
    return BenchmarkSession(Path(session_dir))
