from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union


VALID_STATUSES = {"eligible", "blocked", "incompatible", "supervision-heavy"}


@dataclass(eq=True)
class AdjacencyTruth:
    A_to_B: bool
    B_to_C: bool
    reasons: Optional[Dict[str, str]] = None

    def to_dict(self) -> Dict[str, object]:
        data: Dict[str, object] = {
            "A_to_B": self.A_to_B,
            "B_to_C": self.B_to_C,
        }
        if self.reasons is not None:
            data["reasons"] = dict(self.reasons)
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "AdjacencyTruth":
        return cls(
            A_to_B=bool(data.get("A_to_B", False)),
            B_to_C=bool(data.get("B_to_C", False)),
            reasons=data.get("reasons") if isinstance(data.get("reasons"), dict) else None,
        )


@dataclass(eq=True)
class Supervision:
    profile: str
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, object]:
        out: Dict[str, object] = {"profile": self.profile}
        if self.notes is not None:
            out["notes"] = self.notes
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "Supervision":
        profile = str(data.get("profile", "")).strip()
        notes_val = data.get("notes")
        notes = str(notes_val) if isinstance(notes_val, str) else None
        return cls(profile=profile, notes=notes)


@dataclass(eq=True)
class ThreeStepChain:
    id: str
    tasks: Dict[str, str]
    adjacency: AdjacencyTruth
    benchmark_eligible: bool
    status: str
    supervision: Optional[Supervision] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        self._validate()

    def _validate(self) -> None:
        # Validate tasks have exactly A, B, C
        expected_keys = {"A", "B", "C"}
        task_keys = set(self.tasks.keys())
        if task_keys != expected_keys:
            raise ValueError(f"tasks must contain exactly A,B,C keys, got: {sorted(task_keys)}")
        # Ensure all are non-empty strings
        for k in ("A", "B", "C"):
            v = self.tasks.get(k)
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"Task {k} must be a non-empty string, got: {v!r}")
        # Validate status
        if self.status not in VALID_STATUSES:
            raise ValueError(f"Invalid status {self.status!r}, expected one of {sorted(VALID_STATUSES)}")

    def to_dict(self) -> Dict[str, object]:
        out: Dict[str, object] = {
            "id": self.id,
            "tasks": dict(self.tasks),
            "adjacency": self.adjacency.to_dict(),
            "benchmark_eligible": self.benchmark_eligible,
            "status": self.status,
        }
        if self.supervision is not None:
            out["supervision"] = self.supervision.to_dict()
        if self.notes is not None:
            out["notes"] = self.notes
        return out

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ThreeStepChain":
        tasks_obj = data.get("tasks") or {}
        tasks: Dict[str, str] = {}
        if isinstance(tasks_obj, dict):
            for k in ("A", "B", "C"):
                v = tasks_obj.get(k)
                tasks[k] = str(v) if isinstance(v, str) else ("" if v is None else str(v))

        supervision_obj = data.get("supervision")
        supervision = Supervision.from_dict(supervision_obj) if isinstance(supervision_obj, dict) else None

        adjacency_obj = data.get("adjacency") or {}
        adjacency = AdjacencyTruth.from_dict(adjacency_obj if isinstance(adjacency_obj, dict) else {})

        notes_val = data.get("notes")
        notes = str(notes_val) if isinstance(notes_val, str) else None

        status_val = data.get("status")
        status = str(status_val) if isinstance(status_val, str) else ""

        return cls(
            id=str(data.get("id", "")).strip(),
            tasks=tasks,
            adjacency=adjacency,
            benchmark_eligible=bool(data.get("benchmark_eligible", False)),
            status=status,
            supervision=supervision,
            notes=notes,
        )

    def is_eligible(self) -> bool:
        return (
            self.status == "eligible"
            and self.benchmark_eligible
            and self.adjacency.A_to_B
            and self.adjacency.B_to_C
        )

    def to_runner_payload(self) -> Dict[str, object]:
        # Strict runner payload: exactly three tasks and adjacency booleans only.
        return {
            "chain_id": self.id,
            "tasks": {"A": self.tasks["A"], "B": self.tasks["B"], "C": self.tasks["C"]},
            "adjacency": {"A_to_B": self.adjacency.A_to_B, "B_to_C": self.adjacency.B_to_C},
        }


@dataclass(eq=True)
class ThreeStepManifest:
    chains: List[ThreeStepChain] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return {"chains": [c.to_dict() for c in self.chains]}

    def dumps(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=True, ensure_ascii=False)

    def write_file(self, path: Union[str, Path]) -> Path:
        p = Path(path)
        p.write_text(self.dumps(), encoding="utf-8")
        return p

    @classmethod
    def from_dict(cls, data: Dict[str, object]) -> "ThreeStepManifest":
        chains_raw = data.get("chains") or []
        chains: List[ThreeStepChain] = []
        if isinstance(chains_raw, list):
            for item in chains_raw:
                if isinstance(item, dict):
                    chains.append(ThreeStepChain.from_dict(item))
        return cls(chains=chains)

    @classmethod
    def load_file(cls, path: Union[str, Path]) -> "ThreeStepManifest":
        p = Path(path)
        data = json.loads(p.read_text(encoding="utf-8"))
        return cls.from_dict(data)

    def filter_eligible(self) -> List[ThreeStepChain]:
        return [c for c in self.chains if c.is_eligible()]

    def list_negative_cases(self) -> List[ThreeStepChain]:
        return [c for c in self.chains if c.status in {"blocked", "incompatible", "supervision-heavy"}]

    def to_runner_payloads_for_eligible(self) -> List[Dict[str, object]]:
        return [c.to_runner_payload() for c in self.filter_eligible()]


def _curated_chains() -> List[ThreeStepChain]:
    # Positive / eligible chains (at least two)
    chain_1 = ThreeStepChain(
        id="ch_001_documentation_three_step",
        tasks={
            "A": "tasks/170_orchestrator_default_single_task_path_and_two_task_pilot_gate.md",
            "B": "tasks/171_orchestrator_two_task_pilot_admission_and_eligibility_truth.md",
            "C": "tasks/172_orchestrator_dependency_aware_two_task_handoff_contract.md",
        },
        adjacency=AdjacencyTruth(A_to_B=True, B_to_C=True),
        benchmark_eligible=True,
        status="eligible",
        supervision=Supervision(profile="light", notes="Doc-linked adjacent path with clear handoffs."),
        notes="Curated from two-task pilot admission and handoff truth.",
    )

    chain_2 = ThreeStepChain(
        id="ch_002_three_step_runner_proof",
        tasks={
            "A": "tasks/199_orchestrator_supervised_three_step_canary_admission_and_chain_contract.md",
            "B": "tasks/201_orchestrator_supervised_three_step_canary_runner_and_chain_ledger.md",
            "C": "tasks/203_orchestrator_three_step_canary_benchmark_and_supervision_scorecard.md",
        },
        adjacency=AdjacencyTruth(A_to_B=True, B_to_C=True),
        benchmark_eligible=True,
        status="eligible",
        supervision=Supervision(profile="operator-observed", notes="Direct three-step canary proof path."),
        notes="Intended for supervised chain proof and benchmark linkage.",
    )

    # Negative cases: blocked, incompatible, supervision-heavy
    chain_blocked = ThreeStepChain(
        id="ch_101_blocked_due_to_controller_trace_gap",
        tasks={
            "A": "tasks/204_orchestrator_controller_route_trace_and_resume_reconstruction_for_canary_runs.md",
            "B": "tasks/205_orchestrator_supervised_multi_task_canary_checkpoint_and_adjacent_manifest_gate.md",
            "C": "tasks/203_orchestrator_three_step_canary_benchmark_and_supervision_scorecard.md",
        },
        adjacency=AdjacencyTruth(
            A_to_B=True,
            B_to_C=False,
            reasons={
                "B_to_C": "Benchmark step depends on prior route trace artifacts that are not guaranteed from C.",
            },
        ),
        benchmark_eligible=False,
        status="blocked",
        supervision=Supervision(profile="operator-observed", notes="Route trace artifacts not durable yet."),
        notes="Rejected due to missing downstream artifacts required at C.",
    )

    chain_incompatible = ThreeStepChain(
        id="ch_102_incompatible_handoff",
        tasks={
            "A": "tasks/188b_orchestrator_run_task_dual_transport_selection_and_protected_surface_integration.md",
            "B": "tasks/170_orchestrator_default_single_task_path_and_two_task_pilot_gate.md",
            "C": "tasks/171_orchestrator_two_task_pilot_admission_and_eligibility_truth.md",
        },
        adjacency=AdjacencyTruth(
            A_to_B=False,
            B_to_C=True,
            reasons={"A_to_B": "Transport-focused deliverables do not align with default single-task admission."},
        ),
        benchmark_eligible=False,
        status="incompatible",
        supervision=Supervision(profile="light"),
        notes="First handoff produces incompatible artifact surface.",
    )

    chain_supervision_heavy = ThreeStepChain(
        id="ch_103_supervision_heavy_path",
        tasks={
            "A": "tasks/176_orchestrator_bounded_two_task_pilot_runner_and_pair_ledger.md",
            "B": "tasks/178_orchestrator_supervised_intervention_artifact_and_pilot_failure_digest.md",
            "C": "tasks/180_orchestrator_bounded_two_task_corpus_reproof_and_widening_checkpoint.md",
        },
        adjacency=AdjacencyTruth(
            A_to_B=True,
            B_to_C=True,
            reasons={"notes": "Handoffs require frequent human arbitration of failure digest interpretations."},
        ),
        benchmark_eligible=False,
        status="supervision-heavy",
        supervision=Supervision(
            profile="heavy",
            notes="Requires high-frequency operator arbitration and manual validation of digest artifacts.",
        ),
        notes="Not suitable for benchmark due to heavy supervision requirements.",
    )

    return [chain_1, chain_2, chain_blocked, chain_incompatible, chain_supervision_heavy]


def get_curated_manifest() -> ThreeStepManifest:
    return ThreeStepManifest(chains=_curated_chains())


def dump_curated_manifest(path: Union[str, Path]) -> Path:
    manifest = get_curated_manifest()
    return manifest.write_file(path)


__all__ = [
    "AdjacencyTruth",
    "Supervision",
    "ThreeStepChain",
    "ThreeStepManifest",
    "get_curated_manifest",
    "dump_curated_manifest",
]
