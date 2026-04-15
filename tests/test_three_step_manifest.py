from pathlib import Path

from agents.lib.three_step_manifest import (
    ThreeStepManifest,
    get_curated_manifest,
    dump_curated_manifest,
)


def test_curated_manifest_round_trip(tmp_path: Path) -> None:
    # Dump curated manifest and reload
    out_path = tmp_path / "three_step_curated_manifest.json"
    dump_curated_manifest(out_path)
    loaded = ThreeStepManifest.load_file(out_path)

    # Structural equality against a fresh curated build
    curated = get_curated_manifest()
    assert loaded == curated

    # Round-trip again using write_file on the loaded manifest to ensure serializer stability
    out_path2 = tmp_path / "three_step_curated_manifest_round_2.json"
    loaded.write_file(out_path2)
    loaded2 = ThreeStepManifest.load_file(out_path2)
    assert loaded2 == loaded


def test_eligibility_and_negative_filters() -> None:
    manifest = get_curated_manifest()
    eligible = manifest.filter_eligible()
    negatives = manifest.list_negative_cases()

    # At least two positive/eligible chains
    assert len(eligible) >= 2

    # Negative set contains representative statuses
    negative_statuses = {c.status for c in negatives}
    assert "blocked" in negative_statuses
    assert "incompatible" in negative_statuses
    assert "supervision-heavy" in negative_statuses

    # Eligible chains meet strict criteria
    for c in eligible:
        assert c.status == "eligible"
        assert c.benchmark_eligible is True
        assert c.adjacency.A_to_B is True
        assert c.adjacency.B_to_C is True


def test_runner_payload_shape_and_compatibility() -> None:
    # The runner payload must preserve exactly-three adjacency and not widen scope.
    manifest = get_curated_manifest()
    eligible = manifest.filter_eligible()
    assert eligible, "Expected at least one eligible chain in curated manifest."

    payload = eligible[0].to_runner_payload()

    # Strict top-level keys only
    assert set(payload.keys()) == {"chain_id", "tasks", "adjacency"}

    # Tasks in exact order keys A, B, C
    tasks = payload["tasks"]
    assert isinstance(tasks, dict)
    assert set(tasks.keys()) == {"A", "B", "C"}
    assert all(isinstance(tasks[k], str) and tasks[k] for k in ("A", "B", "C"))

    # Adjacency booleans only
    adjacency = payload["adjacency"]
    assert isinstance(adjacency, dict)
    assert set(adjacency.keys()) == {"A_to_B", "B_to_C"}
    assert isinstance(adjacency["A_to_B"], bool)
    assert isinstance(adjacency["B_to_C"], bool)

    # Import runner module to ensure seam remains compatible without requiring broader scope
    from agents.lib import three_step_canary as canary  # noqa: F401

    # Use the import to avoid unused-import lint and assert module presence
    assert hasattr(canary, "__file__")
