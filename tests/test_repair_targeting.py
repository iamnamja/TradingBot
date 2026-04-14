from pathlib import Path

from agents.lib.repair_targeting import (
    FailureFamily,
    classify_failure_family,
    select_repair_targets,
    persist_classification,
    load_recent_classifications,
    plan_repair_from_evidence,
)


def test_classify_failure_families_by_signal():
    assert classify_failure_family({"missing_deliverables": ["README.md"]}) is FailureFamily.ADMISSION_MISSING_DELIVERABLE
    assert classify_failure_family({"error_type": "ImportError", "message": "cannot import name X"}) is FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE
    assert classify_failure_family({"artifact_mismatch": "path", "message": "artifact not found at two_task/bounded_corpus/pairs.json"}) is FailureFamily.ARTIFACT_PATH_MISMATCH
    assert classify_failure_family({"artifact_mismatch": "shape", "message": "KeyError: missing 'scorecard' in artifact"}) is FailureFamily.ARTIFACT_SHAPE_MISMATCH
    assert classify_failure_family({"benchmark_regression": True}) is FailureFamily.BENCHMARK_COMPAT_REGRESSION
    assert classify_failure_family({"protected_surface_violation": True}) is FailureFamily.STATIC_PROTECTED_VIOLATION
    assert classify_failure_family({"resume_mismatch": True, "message": "checkpoint not found"}) is FailureFamily.RESUME_REENTRY_MISMATCH
    # fallback
    assert classify_failure_family({"message": "some random error"}) is FailureFamily.GENERIC


def _names(targets):
    return [t.name for t in targets]


def test_repair_target_selection_is_narrow_per_family():
    assert _names(select_repair_targets(FailureFamily.ADMISSION_MISSING_DELIVERABLE)) == ["deliverables_only"]
    assert _names(select_repair_targets(FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE)) == ["public_surface_only"]
    assert _names(select_repair_targets(FailureFamily.ARTIFACT_PATH_MISMATCH)) == ["artifact_paths_only"]
    assert _names(select_repair_targets(FailureFamily.ARTIFACT_SHAPE_MISMATCH)) == ["artifact_schema_only"]
    assert _names(select_repair_targets(FailureFamily.BENCHMARK_COMPAT_REGRESSION)) == ["benchmark_harness_only"]
    assert _names(select_repair_targets(FailureFamily.STATIC_PROTECTED_VIOLATION)) == ["compat_alias_or_revert"]
    assert _names(select_repair_targets(FailureFamily.RESUME_REENTRY_MISMATCH)) == ["resume_state_only"]
    assert _names(select_repair_targets(FailureFamily.GENERIC)) == ["minimal_touch_safe_default"]


def test_plan_repair_from_evidence_pairs_classification_and_selection():
    fam, targets = plan_repair_from_evidence({"error_type": "ImportError", "message": "cannot import name Thing"})
    assert fam is FailureFamily.IMPORT_PUBLIC_COMPAT_FAILURE
    assert _names(targets) == ["public_surface_only"]


def test_persist_and_load_classification(tmp_path: Path):
    run_dir = tmp_path / "run"
    run_dir.mkdir(parents=True, exist_ok=True)
    path = persist_classification(run_dir, FailureFamily.ARTIFACT_SHAPE_MISMATCH, {"artifact_mismatch": "shape", "message": "schema mismatch"})
    assert path.exists()
    recs = load_recent_classifications(run_dir)
    assert len(recs) == 1
    r = recs[0]
    assert r.family is FailureFamily.ARTIFACT_SHAPE_MISMATCH
    assert r.short_code == FailureFamily.ARTIFACT_SHAPE_MISMATCH.short_code
    # Evidence tags are persisted as small deterministic labels
    assert any(tag.startswith("msg:") for tag in r.evidence_tags) or "artifact_mismatch" in r.evidence_tags
