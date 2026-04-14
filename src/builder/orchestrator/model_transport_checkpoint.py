from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from agents.lib.docs_status_guard import default_guard_paths, validate_docs_status
from agents.lib.model_profiles import model_profile_registry
from agents.lib.provider_client import negotiate_model_capability


def collect_model_transport_evidence() -> Dict[str, Any]:
    """Collect conservative evidence about docs/model/transport readiness.

    This is additive checkpointing only. It does not mutate runner behavior.
    """
    docs_ok, docs_report = validate_docs_status(default_guard_paths())
    registry = model_profile_registry()

    gpt_bundle = negotiate_model_capability(provider="openai", model="gpt-5", required_transport="file_bundle", allow_fallback=True)
    gpt_method = negotiate_model_capability(provider="openai", model="gpt-5", required_transport="method_insertion", allow_fallback=True)
    codex_patch = negotiate_model_capability(provider="openai", model="gpt-5-codex", required_transport="patch", allow_fallback=False)
    codex_method = negotiate_model_capability(provider="openai", model="gpt-5-codex", required_transport="method_insertion", allow_fallback=True)

    evidence: Dict[str, Any] = {
        "docs_status": {
            "guard_ok": bool(docs_ok),
            "report": docs_report,
        },
        "model_profiles": {
            "registry_size": len(registry),
            "explicit_profiles_present": bool(registry),
            "gpt_profile_present": "gpt_file_bundle" in registry,
            "codex_profile_present": "codex_patch" in registry,
        },
        "transport_support": {
            "gpt_file_bundle_preserved": bool(gpt_bundle.get("compatible", False)),
            "gpt_method_insertion_preserved": bool(gpt_method.get("compatible", False)),
            "codex_patch_declared": bool(codex_patch.get("compatible", False)),
            "codex_method_requires_fallback": bool(codex_method.get("fallback_applied", False)),
        },
        "capability_negotiation": {
            "gpt_file_bundle": gpt_bundle,
            "gpt_method_insertion": gpt_method,
            "codex_patch": codex_patch,
            "codex_method_insertion": codex_method,
        },
    }
    return evidence


def evaluate_model_transport_checkpoint(evidence: Dict[str, Any]) -> Dict[str, Any]:
    docs_status = dict(evidence.get("docs_status") or {})
    profiles = dict(evidence.get("model_profiles") or {})
    transport_support = dict(evidence.get("transport_support") or {})

    docs_ok = bool(docs_status.get("guard_ok", False))
    explicit_profiles = bool(profiles.get("gpt_profile_present", False)) and bool(profiles.get("codex_profile_present", False))
    gpt_preserved = bool(transport_support.get("gpt_file_bundle_preserved", False)) and bool(transport_support.get("gpt_method_insertion_preserved", False))
    codex_available = bool(transport_support.get("codex_patch_declared", False))
    mismatch_diagnostics = bool(transport_support.get("codex_method_requires_fallback", False))

    if not docs_ok or not explicit_profiles or not gpt_preserved:
        verdict = "not_ready"
    elif codex_available and mismatch_diagnostics:
        verdict = "conditionally_ready_under_supervision"
    else:
        verdict = "not_ready"

    return {
        "verdict": verdict,
        "policy": {
            "broad_unattended_multi_task_autonomy": "blocked",
            "standalone_productization": "blocked",
            "next_slice_meaning": "cautious_bounded_planning_only",
        },
        "evaluated_categories": {
            "docs_status_consistency_enforcement": docs_ok,
            "model_profile_explicitness": explicit_profiles,
            "codex_transport_availability": codex_available,
            "mismatch_diagnostics_and_fallback": mismatch_diagnostics,
            "proven_gpt_file_bundle_path_preserved": gpt_preserved,
        },
        "notes": (
            "Checkpoint is conservative. Conditioned readiness only means a cautious bounded next slice may be planned. "
            "It does not unblock unattended autonomy or standalone productization."
        ),
    }


def write_model_transport_checkpoint(base_dir: str, evaluation: Dict[str, Any], evidence_snapshot: Optional[Dict[str, Any]] = None) -> str:
    reliability_dir = os.path.join(base_dir, "reliability")
    os.makedirs(reliability_dir, exist_ok=True)
    checkpoint_path = os.path.join(reliability_dir, "model_transport_checkpoint.json")

    payload: Dict[str, Any] = {
        "checkpoint_kind": "contract_and_model_transport_checkpoint",
        "evaluation": evaluation,
    }
    if evidence_snapshot is not None:
        payload["evidence"] = evidence_snapshot

    with open(checkpoint_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, sort_keys=True)

    return checkpoint_path


__all__ = [
    "collect_model_transport_evidence",
    "evaluate_model_transport_checkpoint",
    "write_model_transport_checkpoint",
]
