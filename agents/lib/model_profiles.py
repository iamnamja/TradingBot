from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Dict, Mapping, Tuple

# Public transport kinds (stable vocabulary)
TRANSPORT_FILE_BUNDLE = "file_bundle"
TRANSPORT_PATCH = "patch"

# Public transport contracts (stable vocabulary)
CONTRACT_STRICT_FILE_BUNDLE = "strict_file_bundle"
CONTRACT_PATCH_APPLY_MODE = "patch_apply_mode"


@dataclass(frozen=True)
class ModelProfile:
    id: str
    display_name: str
    family: str
    output_transport: str
    transport_contract: str
    notes: str = ""

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


# Canonical profile registry keyed by profile id
# Keep small and explicit; default path remains GPT-style strict file-bundle mode.
_PROFILE_REGISTRY: Dict[str, ModelProfile] = {
    "gpt_file_bundle": ModelProfile(
        id="gpt_file_bundle",
        display_name="GPT-style file-bundle",
        family="gpt",
        output_transport=TRANSPORT_FILE_BUNDLE,
        transport_contract=CONTRACT_STRICT_FILE_BUNDLE,
        notes="Strict BEGIN_FILE_BUNDLE/FILE:/END_FILE/END_FILE_BUNDLE transport. Known-good default path.",
    ),
    "codex_patch": ModelProfile(
        id="codex_patch",
        display_name="Codex-style patch/apply",
        family="codex",
        output_transport=TRANSPORT_PATCH,
        transport_contract=CONTRACT_PATCH_APPLY_MODE,
        notes="Patch/diff-style transport. Not enabled by default in the runner yet.",
    ),
}


def model_profile_registry() -> Dict[str, Dict[str, object]]:
    """
    Return a mapping of profile id -> profile metadata as plain dicts.
    """
    return {k: v.to_dict() for k, v in _PROFILE_REGISTRY.items()}


def get_profile_by_id(profile_id: str, default: str = "gpt_file_bundle") -> Dict[str, object]:
    """
    Resolve a profile by id; fall back to the GPT file-bundle profile.
    """
    pid = (profile_id or "").strip() or default
    profile = _PROFILE_REGISTRY.get(pid) or _PROFILE_REGISTRY.get(default)
    return profile.to_dict() if profile else {}


def _coerce_provider_model(provider: str | None, model: str | None) -> Tuple[str, str]:
    p = (provider or "").strip().lower()
    m = (model or "").strip().lower()
    return p, m


def _infer_profile_id_for_model(provider: str | None, model: str | None) -> str:
    """
    Conservative inference with safe default:
    - If model name contains 'codex' → codex_patch
    - Otherwise → gpt_file_bundle
    Notes:
    - Keep logic explicit and minimal; wider coverage can be added as we integrate more models.
    """
    _provider, m = _coerce_provider_model(provider, model)
    if "codex" in m:
        return "codex_patch"
    return "gpt_file_bundle"


def get_model_profile(provider: str | None, model: str | None) -> Dict[str, object]:
    """
    Return the explicit profile metadata for the given provider/model.
    Defaults to GPT-style strict file-bundle transport.
    """
    profile_id = _infer_profile_id_for_model(provider, model)
    return get_profile_by_id(profile_id)


def output_transport_from_profile(profile: Mapping[str, Any] | None) -> str:
    """
    Convenience accessor for the output transport from a profile payload.
    """
    payload = dict(profile or {})
    transport = str(payload.get("output_transport", "") or "").strip()
    if transport in {TRANSPORT_FILE_BUNDLE, TRANSPORT_PATCH}:
        return transport
    # Safe default preserves known-good GPT path
    return TRANSPORT_FILE_BUNDLE


def transport_contract_from_profile(profile: Mapping[str, Any] | None) -> str:
    """
    Convenience accessor for the transport contract from a profile payload.
    """
    payload = dict(profile or {})
    contract = str(payload.get("transport_contract", "") or "").strip()
    if contract in {CONTRACT_STRICT_FILE_BUNDLE, CONTRACT_PATCH_APPLY_MODE}:
        return contract
    # Safe default preserves known-good GPT path
    return CONTRACT_STRICT_FILE_BUNDLE
