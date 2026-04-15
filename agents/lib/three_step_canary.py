from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class CanaryTask:
    id: str
    follows: Optional[str]
    admitted: bool = False


@dataclass
class AdjacentPairTruth:
    from_id: str
    to_id: str
    follows_expected: str
    follows_actual: Optional[str]
    adjacency_ok: bool
    resume: Dict[str, Any]


@dataclass
class ChainLedger:
    session_id: str
    created_at_epoch_utc: float
    tasks_order: List[str]
    tasks: List[Dict[str, Any]]
    admitted_all: bool
    supervision: Dict[str, Any]
    adjacency: Dict[str, AdjacentPairTruth]
    terminal_outcome: str
    stopped_reason: Optional[str] = None

    def to_json(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "created_at_epoch_utc": self.created_at_epoch_utc,
            "tasks_order": self.tasks_order,
            "tasks": self.tasks,
            "admitted_all": self.admitted_all,
            "supervision": self.supervision,
            "adjacency": {
                k: asdict(v) for k, v in self.adjacency.items()
            },
            "terminal_outcome": self.terminal_outcome,
            "stopped_reason": self.stopped_reason,
        }


def _ensure_three(tasks: List[Dict[str, Any]]) -> Tuple[List[CanaryTask], Optional[str]]:
    if len(tasks) != 3:
        return [], f"exactly_three_tasks_required: got {len(tasks)}"
    conv: List[CanaryTask] = []
    for t in tasks:
        conv.append(
            CanaryTask(
                id=str(t.get("id")),
                follows=t.get("follows"),
                admitted=bool(t.get("admitted", False)),
            )
        )
    return conv, None


def _adjacency_truth(
    a: CanaryTask,
    b: CanaryTask,
    resume_state: Optional[Dict[str, Any]] = None,
) -> AdjacentPairTruth:
    resume_info = {
        "resumed": False,
        "checkpoint": None,
        "resume_mode": "fresh",
    }
    if resume_state:
        # Normalize expected fields, defaulting conservatively
        resume_info["resumed"] = bool(resume_state.get("resumed", False))
        resume_info["checkpoint"] = resume_state.get("checkpoint")
        resume_info["resume_mode"] = str(resume_state.get("resume_mode", "fresh"))
    return AdjacentPairTruth(
        from_id=a.id,
        to_id=b.id,
        follows_expected=a.id,
        follows_actual=b.follows,
        adjacency_ok=(b.follows == a.id),
        resume=resume_info,
    )


def _write_ledger(
    artifacts_dir: str,
    session_id: str,
    ledger: ChainLedger,
) -> str:
    session_dir = os.path.join(artifacts_dir, "three_step_canary", session_id)
    os.makedirs(session_dir, exist_ok=True)
    ledger_path = os.path.join(session_dir, "chain_ledger.json")
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger.to_json(), f, indent=2, sort_keys=True)
    return ledger_path


def validate_three_step_manifest(tasks: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    converted, err = _ensure_three(tasks)
    if err:
        return False, err
    a, b, c = converted
    if not (a.admitted and b.admitted and c.admitted):
        return False, "all_three_tasks_must_be_explicitly_admitted"
    if b.follows != a.id:
        return False, f"strict_adjacency_required_A_to_B: expected {a.id} got {b.follows}"
    if c.follows != b.id:
        return False, f"strict_adjacency_required_B_to_C: expected {b.id} got {c.follows}"
    return True, None


def run_three_step_canary(
    tasks: List[Dict[str, Any]],
    artifacts_dir: str,
    *,
    supervision_required: bool = True,
    resume_pairs: Optional[Dict[str, Dict[str, Any]]] = None,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Supervised three-step canary runner for exactly three adjacent tasks.

    Behavior:
    - Requires exactly 3 tasks.
    - Requires all tasks admitted == True.
    - Requires strict adjacency: B.follows == A.id and C.follows == B.id.
    - Supervision is mandatory; if supervision_required is False, the chain is rejected.
    - Persists a durable chain ledger capturing admission, adjacency, supervision, resume truth, and terminal outcome.

    Returns a dict with:
      - ok: bool (True only when accepted)
      - outcome: str ('accepted' or 'rejected')
      - session_id: str
      - ledger_path: str (path to durable ledger)
      - reason: Optional[str]
    """
    if session_id is None:
        session_id = uuid.uuid4().hex

    converted, shape_err = _ensure_three(tasks)
    if shape_err:
        # Enforce exactly-three hard gate via exception per acceptance criteria strictness
        raise ValueError(shape_err)

    a, b, c = converted
    admitted_all = a.admitted and b.admitted and c.admitted

    # Evaluate adjacency with provided resume truth
    rp = resume_pairs or {}
    adj_ab = _adjacency_truth(a, b, rp.get("A_to_B") or rp.get("A->B"))
    adj_bc = _adjacency_truth(b, c, rp.get("B_to_C") or rp.get("B->C"))

    supervision = {
        "required": True,
        "mode": "supervised" if supervision_required else "unsupervised_requested",
        "no_manual_intervention": True,
    }

    # Determine terminal outcome conservatively
    outcome = "accepted"
    stopped_reason: Optional[str] = None

    if not supervision_required:
        outcome = "rejected"
        stopped_reason = "supervision_required"

    if outcome == "accepted" and not admitted_all:
        outcome = "rejected"
        stopped_reason = "all_three_tasks_must_be_explicitly_admitted"

    if outcome == "accepted" and not adj_ab.adjacency_ok:
        outcome = "rejected"
        stopped_reason = "strict_adjacency_required_A_to_B"

    if outcome == "accepted" and not adj_bc.adjacency_ok:
        outcome = "rejected"
        stopped_reason = "strict_adjacency_required_B_to_C"

    ledger = ChainLedger(
        session_id=session_id,
        created_at_epoch_utc=time.time(),
        tasks_order=[a.id, b.id, c.id],
        tasks=[
            {"id": a.id, "follows": a.follows, "admitted": a.admitted, "order": 0},
            {"id": b.id, "follows": b.follows, "admitted": b.admitted, "order": 1},
            {"id": c.id, "follows": c.follows, "admitted": c.admitted, "order": 2},
        ],
        admitted_all=admitted_all,
        supervision=supervision,
        adjacency={"A_to_B": adj_ab, "B_to_C": adj_bc},
        terminal_outcome=outcome,
        stopped_reason=stopped_reason,
    )

    ledger_path = _write_ledger(artifacts_dir, session_id, ledger)

    return {
        "ok": outcome == "accepted",
        "outcome": outcome,
        "session_id": session_id,
        "ledger_path": ledger_path,
        "reason": stopped_reason,
    }
