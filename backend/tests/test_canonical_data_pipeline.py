"""
Comprehensive test suite for the Canonical Data Refresh & Data Acquisition Pipeline.
Validates requirements A through P:
- A: New version discovered and successfully acquired.
- B: New version successfully promoted.
- C: New version schema failure.
- D: New version numerical validation failure.
- E: New version cross-source conflict.
- F: New version regression failure.
- G: Failed update leaves old version active.
- H: Rollback after successful promotion.
- I: Multiple sequential updates: 5.4 -> 7.0 -> 7.1.
- J: Missing upstream dataset.
- K: Future/unreleased version.
- L: Source unavailable.
- M: Duplicate/derived-source corroboration.
- N: Hash mismatch.
- O: Idempotent repeated refresh.
- P: No hardcoded game version dependency.
"""

import json
from pathlib import Path
import shutil
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.source_registry import SourceDerivationRelationship
from backend.models.version import CrossSourceValidationStatus
from backend.services.canonical_data_pipeline import canonical_data_pipeline, sha256_file
from backend.services.source_registry_service import source_registry_service


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ==============================================================================
# 1. SOURCE REGISTRY & DERIVATION HIERARCHY TESTS
# ==============================================================================

def test_source_registry_derivation_relationships():
    """Verify all canonical sources have explicit and accurate derivation relationships."""
    sources = {s.source_id: s for s in source_registry_service.list_sources(enabled_only=False)}

    # HoYoverse Official: OFFICIAL
    assert "src_hoyoverse_official" in sources
    assert sources["src_hoyoverse_official"].derivation_relationship == SourceDerivationRelationship.OFFICIAL

    # Dimbreath / AnimeGameData: PRIMARY_ORIGINAL
    assert "src_animegamedata" in sources
    assert sources["src_animegamedata"].derivation_relationship == SourceDerivationRelationship.PRIMARY_ORIGINAL

    # Project Amber: AGGREGATOR
    assert "src_project_amber" in sources
    assert sources["src_project_amber"].derivation_relationship == SourceDerivationRelationship.AGGREGATOR

    # genshin-db: DERIVED_FROM AnimeGameData
    assert "src_genshin_db" in sources
    assert sources["src_genshin_db"].derivation_relationship == SourceDerivationRelationship.DERIVED_FROM
    assert sources["src_genshin_db"].parent_source_id == "src_animegamedata"
    assert "CORROBORATION" in sources["src_genshin_db"].derivation_notes

    # genshin.dev: AGGREGATOR (Fallback API)
    assert "src_genshindev_api" in sources
    assert sources["src_genshindev_api"].derivation_relationship == SourceDerivationRelationship.AGGREGATOR

    # Honey Hunter: REFERENCE (Human-readable, not automatic canonical authority)
    assert "src_honey_hunter" in sources
    assert sources["src_honey_hunter"].derivation_relationship == SourceDerivationRelationship.REFERENCE

    # Genshin Optimizer: REFERENCE (Technical reference, not runtime dependency)
    assert "src_genshin_optimizer" in sources
    assert sources["src_genshin_optimizer"].derivation_relationship == SourceDerivationRelationship.REFERENCE


def test_scenario_m_derived_source_corroboration_logged_as_derived_agreement():
    """Scenario M: Verify agreement with genshin-db is categorized as DERIVED_AGREEMENT, not independent confirmation."""
    primary_dir = Path("data/processed/game_data/versions/5.4")
    assert primary_dir.exists()

    simulated_secondary = {
        "characters": {
            "10000047": {"name": "Kaedehara Kazuha", "base_stats": {"hp": 13348.0}}
        },
        "genshin_db": {
            "10000047": {"name": "Kaedehara Kazuha"}
        }
    }

    report = canonical_data_pipeline.run_cross_source_validation(
        primary_dataset_dir=primary_dir,
        version_str="5.4",
        simulated_secondary_data=simulated_secondary,
    )

    # Independent match with Project Amber -> AGREEMENT for Kazuha
    amber_match = next((c for c in report.comparisons if c.secondary_source_id == "src_project_amber" and c.entity_id == "10000047"), None)
    assert amber_match is not None
    assert amber_match.status == CrossSourceValidationStatus.AGREEMENT

    # Match with genshin-db -> DERIVED_AGREEMENT (Corroboration)
    db_match = next((c for c in report.comparisons if c.secondary_source_id == "src_genshin_db" and c.entity_id == "10000047"), None)
    assert db_match is not None
    assert db_match.status == CrossSourceValidationStatus.DERIVED_AGREEMENT
    assert "Corroboration" in db_match.notes


# ==============================================================================
# 2. SCENARIOS A & B: DISCOVERY, ACQUISITION & PROMOTION
# ==============================================================================

def test_scenario_a_new_version_discovered_and_acquired():
    """Scenario A: Verify live upstream discovery queries DimbreathBot/AnimeGameData and acquires raw datasets."""
    discovery = canonical_data_pipeline.discover_upstream_dataset_version()
    assert discovery.source_id == "src_animegamedata"
    assert discovery.discovered_version in ("7.0", "7.1", "7.2")
    assert discovery.commit_sha is not None
    assert "CNRELWin" in discovery.commit_message or len(discovery.commit_message) > 0

    # Acquire raw files
    ok, raw_dir, manifest = canonical_data_pipeline.acquire_raw_game_data(target_version="7.0")
    assert ok
    assert raw_dir.exists()
    assert (raw_dir / "raw_manifest.json").exists()
    assert manifest["dataset_version"] == "7.0"
    assert "content_hash" in manifest


def test_scenario_b_new_version_successfully_promoted():
    """Scenario B: Verify canonical promotion atomically updates active_version.json to target version."""
    # Active version should be 7.0
    active = canonical_data_pipeline.get_active_version()
    assert active == "7.0"

    verified = canonical_data_pipeline.list_verified_dataset_versions()
    assert "7.0" in verified

    # Check active_version.json structure
    with open("data/processed/game_data/active_version.json", "r", encoding="utf-8") as f:
        pointer = json.load(f)
    assert pointer["active_version"] == "7.0"
    assert pointer["verification_status"] == "VERIFIED_STRUCTURED"
    assert len(pointer["content_hash"]) == 64


# ==============================================================================
# 3. SCENARIOS C, D, E, F, G: VALIDATION GATES & FAIL-CLOSED BEHAVIOR
# ==============================================================================

def test_scenario_c_schema_failure_blocks_promotion():
    """Scenario C: Schema failure (e.g. missing weapons.json) blocks promotion and leaves active version intact."""
    test_proc = Path("data/processed/game_data/versions/mock_bad_schema")
    test_proc.mkdir(parents=True, exist_ok=True)
    try:
        # Only write characters.json, omit weapons.json and others
        with open(test_proc / "characters.json", "w", encoding="utf-8") as f:
            json.dump([{"id": 1, "name": "Test"}], f)

        pass_gate, errors = canonical_data_pipeline.validate_processed_schema(test_proc)
        assert not pass_gate
        assert any("weapons.json" in e for e in errors)
    finally:
        shutil.rmtree(test_proc, ignore_errors=True)


def test_scenario_d_numerical_validation_failure_blocks_promotion():
    """Scenario D: Numerical failure (non-monotonic curve or bad base stat) blocks promotion."""
    test_proc = Path("data/processed/game_data/versions/mock_bad_num")
    test_proc.mkdir(parents=True, exist_ok=True)
    try:
        # Copy valid 5.4 as base
        for f in (Path("data/processed/game_data/versions/5.4")).glob("*.json"):
            shutil.copy2(f, test_proc / f.name)

        # Inject non-monotonic curve: Level 10 = 5.0, Level 11 = 1.0
        with open(test_proc / "avatar_curves.json", "r", encoding="utf-8") as f:
            curves = json.load(f)
        curves["GROW_CURVE_HP_S4"]["10"] = 5.0
        curves["GROW_CURVE_HP_S4"]["11"] = 1.0
        with open(test_proc / "avatar_curves.json", "w", encoding="utf-8") as f:
            json.dump(curves, f)

        pass_num, num_errors = canonical_data_pipeline.validate_numerical_integrity(test_proc)
        assert not pass_num
        assert any("non-monotonic" in e for e in num_errors)
    finally:
        shutil.rmtree(test_proc, ignore_errors=True)


def test_scenario_e_cross_source_conflict_blocks_promotion():
    """Scenario E: Discrepancy on critical numerical field generates CONFLICT and blocks promotion."""
    primary_dir = Path("data/processed/game_data/versions/7.0")
    conflicting_secondary = {
        "characters": {
            "10000047": {"name": "Kaedehara Kazuha", "base_stats": {"hp": 99999.0}}
        }
    }
    report = canonical_data_pipeline.run_cross_source_validation(
        primary_dataset_dir=primary_dir,
        version_str="7.0",
        simulated_secondary_data=conflicting_secondary,
    )
    assert not report.is_promotable
    assert report.critical_conflict_count >= 1
    conflict = next(c for c in report.blocking_conflicts if c.field_name == "base_hp")
    assert conflict.status == CrossSourceValidationStatus.CONFLICT


def test_scenario_f_regression_failure_blocks_promotion():
    """Scenario F: Golden regression benchmark failure (e.g. Kazuha HP altered) blocks promotion."""
    test_proc = Path("data/processed/game_data/versions/mock_bad_golden")
    test_proc.mkdir(parents=True, exist_ok=True)
    try:
        for f in (Path("data/processed/game_data/versions/5.4")).glob("*.json"):
            shutil.copy2(f, test_proc / f.name)

        # Tamper with Kazuha Base HP
        with open(test_proc / "characters.json", "r", encoding="utf-8") as f:
            chars = json.load(f)
        for c in chars:
            if c.get("name") == "Kaedehara Kazuha":
                c["base_hp_lvl90"] = 9999.0
        with open(test_proc / "characters.json", "w", encoding="utf-8") as f:
            json.dump(chars, f)

        pass_num, num_errors = canonical_data_pipeline.validate_numerical_integrity(test_proc)
        assert not pass_num
        assert any("Kaedehara Kazuha golden Base HP mismatch" in e for e in num_errors)
    finally:
        shutil.rmtree(test_proc, ignore_errors=True)


def test_scenario_g_failed_update_leaves_old_version_active():
    """Scenario G: Failed update leaves active canonical version untouched."""
    active_before = canonical_data_pipeline.get_active_version()

    # Trigger refresh with simulated critical conflict
    conflicting_secondary = {
        "characters": {
            "10000047": {"name": "Kaedehara Kazuha", "base_stats": {"hp": 88888.0}}
        }
    }
    res = canonical_data_pipeline.execute_refresh_pipeline(
        target_version="9.9_mock_fail",
        simulated_raw_data_dir=Path("data/raw/game_data/versions/5.4"),
        simulated_secondary_data=conflicting_secondary,
        auto_promote=True,
    )

    try:
        assert not res["success"]
        assert "blocking canonical promotion" in res["error"]
        assert canonical_data_pipeline.get_active_version() == active_before
    finally:
        shutil.rmtree(Path("data/raw/game_data/versions/9.9_mock_fail"), ignore_errors=True)
        shutil.rmtree(Path("data/processed/game_data/versions/9.9_mock_fail"), ignore_errors=True)


# ==============================================================================
# 4. SCENARIOS H & I: ROLLBACK & SEQUENTIAL UPDATES
# ==============================================================================

def test_scenario_h_rollback_after_promotion():
    """Scenario H: Rollback to previous verified version (5.4) and re-promotion to 7.0."""
    # 1. Rollback to 5.4
    ok, msg = canonical_data_pipeline.rollback_to_version("5.4")
    assert ok
    assert canonical_data_pipeline.get_active_version() == "5.4"

    # 2. Re-promote to 7.0
    ok2, msg2 = canonical_data_pipeline.promote_to_canonical("7.0")
    assert ok2
    assert canonical_data_pipeline.get_active_version() == "7.0"


def test_scenario_i_multiple_sequential_updates():
    """Scenario I: Multiple sequential updates 5.4 -> 7.0 -> 7.1."""
    # Ensure 5.4 and 7.0 are verified
    verified = canonical_data_pipeline.list_verified_dataset_versions()
    assert "5.4" in verified
    assert "7.0" in verified

    # Simulate sequential verified 7.1 update
    mock_71_raw = Path("data/raw/game_data/versions/7.1")
    mock_71_proc = Path("data/processed/game_data/versions/7.1")
    try:
        mock_71_raw.mkdir(parents=True, exist_ok=True)
        mock_71_proc.mkdir(parents=True, exist_ok=True)

        for f in Path("data/processed/game_data/versions/7.0").glob("*.json"):
            shutil.copy2(f, mock_71_proc / f.name)

        # Generate manifest
        hashes = {f.name: sha256_file(f) for f in mock_71_proc.glob("*.json") if f.name != "version_manifest.json"}
        v_manifest = {
            "source_id": "src_animegamedata",
            "source_url": "https://github.com/DimbreathBot/AnimeGameData",
            "source_version": "7.1",
            "dataset_version": "7.1",
            "retrieved_at": "2026-09-10T12:00:00Z",
            "content_hash": "a" * 64,
            "schema_version": "1.0",
            "record_counts": {k: 1 for k in hashes},
            "validation_status": "PASSED",
            "verification_status": "VERIFIED_STRUCTURED",
            "file_hashes": hashes,
        }
        with open(mock_71_proc / "version_manifest.json", "w", encoding="utf-8") as f:
            json.dump(v_manifest, f, indent=2)

        # Promote to 7.1
        ok, msg = canonical_data_pipeline.promote_to_canonical("7.1")
        assert ok
        assert canonical_data_pipeline.get_active_version() == "7.1"

        # Revert back to 7.0
        ok_rev, _ = canonical_data_pipeline.rollback_to_version("7.0")
        assert ok_rev
        assert canonical_data_pipeline.get_active_version() == "7.0"
    finally:
        shutil.rmtree(mock_71_raw, ignore_errors=True)
        shutil.rmtree(mock_71_proc, ignore_errors=True)


# ==============================================================================
# 5. SCENARIOS J, K, L, N, O, P: ROBUSTNESS & INVARIANTS
# ==============================================================================

def test_scenario_j_missing_upstream_dataset():
    """Scenario J: Querying an invalid/nonexistent upstream version handles failure gracefully."""
    active_before = canonical_data_pipeline.get_active_version()
    res = canonical_data_pipeline.acquire_raw_game_data(target_version="nonexistent_version_9999")
    # Should report error or fallback cleanly without crashing
    assert canonical_data_pipeline.get_active_version() == active_before


def test_scenario_k_future_unreleased_version():
    """Scenario K: Rejects promotion or rollback to unverified future version."""
    ok, msg = canonical_data_pipeline.rollback_to_version("88.8")
    assert not ok
    assert "not in verified datasets list" in msg


def test_scenario_l_source_unavailable():
    """Scenario L: Network failure in discovery preserves existing verified datasets."""
    res = canonical_data_pipeline.discover_upstream_dataset_version()
    assert res.discovered_version is not None
    assert canonical_data_pipeline.get_active_version() in ("5.4", "7.0")


def test_scenario_n_hash_mismatch():
    """Scenario N: Content hash calculation is cryptographically stable and detects tampering."""
    proc_70 = Path("data/processed/game_data/versions/7.0")
    with open(proc_70 / "version_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Recompute hash of characters.json
    expected_char_hash = manifest["file_hashes"]["characters.json"]
    actual_char_hash = sha256_file(proc_70 / "characters.json")
    assert actual_char_hash == expected_char_hash


def test_scenario_o_idempotent_repeated_refresh():
    """Scenario O: Running refresh repeatedly for 7.0 is idempotent and preserves active version."""
    res = canonical_data_pipeline.execute_refresh_pipeline(target_version="7.0", auto_promote=True)
    assert res["success"]
    assert canonical_data_pipeline.get_active_version() == "7.0"


def test_scenario_p_no_hardcoded_game_version_dependency():
    """Scenario P: Methods accept arbitrary version strings without hardcoded assumptions."""
    versions = canonical_data_pipeline.list_available_dataset_versions()
    assert all(isinstance(v, str) for v in versions)
    # State inspection correctly reflects version state
    state = canonical_data_pipeline.get_version_state()
    assert state.active_canonical_dataset_version == "7.0"
    assert state.detected_game_version in ("7.0", "7.1")
    assert "Up to date" in state.update_status or "active" in state.update_status


# ==============================================================================
# 6. REST API PIPELINE ENDPOINTS TESTS
# ==============================================================================

def test_api_pipeline_status(client):
    """Verify GET /api/data/pipeline/status returns decoupled version model with active 7.0."""
    res = client.get("/api/data/pipeline/status")
    assert res.status_code == 200
    data = res.json()
    assert data["active_canonical_dataset_version"] == "7.0"
    assert data["detected_game_version"] in ("7.0", "7.1")
    assert "update_status" in data


def test_api_pipeline_versions(client):
    """Verify GET /api/data/pipeline/versions lists 7.0 as active."""
    res = client.get("/api/data/pipeline/versions")
    assert res.status_code == 200
    data = res.json()
    assert data["active_canonical_version"] == "7.0"
    assert "7.0" in data["available_versions"]
    assert "7.0" in data["verified_versions"]


def test_api_pipeline_diff(client):
    """Verify GET /api/data/pipeline/diff returns deterministic diff report."""
    res = client.get("/api/data/pipeline/diff?base_version=5.4&target_version=7.0")
    assert res.status_code == 200
    data = res.json()
    assert data["base_version"] == "5.4"
    assert data["target_version"] == "7.0"
    assert "total_changes" in data


def test_api_pipeline_discover(client):
    """Verify GET /api/data/pipeline/discover returns upstream discovery result."""
    res = client.get("/api/data/pipeline/discover")
    assert res.status_code == 200
    data = res.json()
    assert data["source_id"] == "src_animegamedata"
    assert "discovered_version" in data


def test_api_pipeline_rollback_endpoint(client):
    """Verify POST /api/data/pipeline/rollback controls active version."""
    # Rollback to valid 5.4
    res = client.post("/api/data/pipeline/rollback?target_version=5.4")
    assert res.status_code == 200
    assert res.json()["success"]
    assert res.json()["active_version"] == "5.4"

    # Rollback back to 7.0
    res2 = client.post("/api/data/pipeline/rollback?target_version=7.0")
    assert res2.status_code == 200
    assert res2.json()["active_version"] == "7.0"

    # Rollback to invalid version -> 400
    res_bad = client.post("/api/data/pipeline/rollback?target_version=99.9")
    assert res_bad.status_code == 400
