from __future__ import annotations

from agents.lib import provider_client as pc
from agents.lib import model_profiles as mp


def test_registry_contains_min_profiles():
    reg = mp.model_profile_registry()
    assert "gpt_file_bundle" in reg
    assert "codex_patch" in reg
    assert reg["gpt_file_bundle"]["output_transport"] == mp.TRANSPORT_FILE_BUNDLE
    assert reg["gpt_file_bundle"]["transport_contract"] == mp.CONTRACT_STRICT_FILE_BUNDLE
    assert reg["codex_patch"]["output_transport"] == mp.TRANSPORT_PATCH
    assert reg["codex_patch"]["transport_contract"] == mp.CONTRACT_PATCH_APPLY_MODE


def test_gpt_style_profile_defaults_to_file_bundle():
    # Using a default GPT-style model id
    profile = mp.get_model_profile("openai", "gpt-5")
    assert profile["id"] == "gpt_file_bundle"
    assert mp.output_transport_from_profile(profile) == mp.TRANSPORT_FILE_BUNDLE
    assert mp.transport_contract_from_profile(profile) == mp.CONTRACT_STRICT_FILE_BUNDLE

    # Provider client wrapper should surface the same outcome
    decl = pc.declared_transport_contract(provider="openai", model="gpt-5")
    assert decl["output_transport"] == mp.TRANSPORT_FILE_BUNDLE
    assert decl["transport_contract"] == mp.CONTRACT_STRICT_FILE_BUNDLE


def test_codex_style_profile_declares_patch_transport():
    # A codex-style model id should map to patch/apply transport
    profile = mp.get_model_profile("openai", "gpt-5-codex")
    assert profile["id"] == "codex_patch"
    assert mp.output_transport_from_profile(profile) == mp.TRANSPORT_PATCH
    assert mp.transport_contract_from_profile(profile) == mp.CONTRACT_PATCH_APPLY_MODE

    # Provider client wrapper should surface the same outcome
    decl = pc.declared_transport_contract(provider="openai", model="gpt-5-codex")
    assert decl["output_transport"] == mp.TRANSPORT_PATCH
    assert decl["transport_contract"] == mp.CONTRACT_PATCH_APPLY_MODE


def test_unknown_model_falls_back_to_gpt_file_bundle():
    profile = mp.get_model_profile("anthropic", "some-unknown-model-id")
    assert profile["id"] == "gpt_file_bundle"
    assert mp.output_transport_from_profile(profile) == mp.TRANSPORT_FILE_BUNDLE
    assert mp.transport_contract_from_profile(profile) == mp.CONTRACT_STRICT_FILE_BUNDLE

    # Wrapper fallback as well
    assert pc.output_transport_for_model(provider="anthropic", model="some-unknown-model-id") == mp.TRANSPORT_FILE_BUNDLE
    assert pc.transport_contract_for_model(provider="anthropic", model="some-unknown-model-id") == mp.CONTRACT_STRICT_FILE_BUNDLE
