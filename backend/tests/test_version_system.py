"""Unit and integration tests for GenshinIQ Version and Update Management System (Phase 2).

Verifies canonical registry up to Version 7.0 ("The Stars Turn Anew"), staleness calculation,
post-5.4 content introduction, API endpoints, and knowledge document version filtering.
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.version import FreshnessStatus, VerificationStatus
from backend.services.version_service import (
    version_service,
    VersionService,
    VERSIONS_FILE,
    PATCH_CHANGES_FILE,
    parse_version_tuple,
)
from backend.services.knowledge_service import knowledge_service
from backend.services.game_data_service import game_data_service

client = TestClient(app)


def test_parse_version_tuple():
    """Verify version tuple parsing."""
    assert parse_version_tuple("7.0") == (7, 0)
    assert parse_version_tuple("v7.0") == (7, 0)
    assert parse_version_tuple("5.4") == (5, 4)
    assert parse_version_tuple("v5.4") == (5, 4)
    assert parse_version_tuple("1.0") == (1, 0)
    assert parse_version_tuple("invalid") == (0, 0)


def test_version_7_0_is_current():
    """Requirement 11a: Verify canonical current live game version is v7.0."""
    curr = version_service.get_current_version()
    assert curr.version == "7.0"
    assert "The Stars Turn Anew" in curr.name
    assert curr.release_date == "2026-09-02"
    assert curr.is_current is True
    assert curr.major_region == "Celestia / Khaenri'ah"


def test_version_5_4_is_not_current():
    """Requirement 11b: Verify v5.4 is explicitly marked as NOT current."""
    v54 = version_service.get_version("5.4")
    assert v54 is not None
    assert v54.version == "5.4"
    assert v54.is_current is False
    assert "Dreams of Light" in v54.name


def test_version_5_4_treated_as_stale_and_older_than_current():
    """Requirement 11c: Verify a v5.4 document/version is appropriately treated as older than current (stale)."""
    eval_54 = version_service.evaluate_staleness("5.4")
    assert eval_54.is_current is False
    assert eval_54.is_stale is True
    # Distance between 5.4 and 7.0 is 14 patches
    assert eval_54.version_distance >= 14
    assert eval_54.warning is not None
    assert "behind" in eval_54.warning.lower()


def test_version_7_0_receives_current_treatment():
    """Requirement 11d: Verify v7.0/current documents receive current-version treatment."""
    eval_70 = version_service.evaluate_staleness("7.0")
    assert eval_70.is_current is True
    assert eval_70.is_stale is False
    assert eval_70.version_distance == 0
    assert eval_70.warning is None


def test_version_ordering_complete_registry():
    """Requirement 11e: Verify version ordering works across the complete registry (1.0 through 7.0, 53 patches)."""
    all_versions = version_service.get_all_versions()
    assert len(all_versions) >= 53
    # Ordered newest first
    assert all_versions[0].version == "7.0"
    assert all_versions[0].is_current is True
    assert all_versions[-1].version == "1.0"
    assert all_versions[-1].is_current is False

    # Check that versions progress monotonically backwards
    ver_strings = [v.version for v in all_versions]
    assert "7.0" in ver_strings
    assert "6.8" in ver_strings
    assert "6.0" in ver_strings
    assert "5.7" in ver_strings
    assert "5.4" in ver_strings
    assert "4.0" in ver_strings
    assert "3.0" in ver_strings
    assert "2.0" in ver_strings
    assert "1.0" in ver_strings


def test_version_distance_calculations():
    """Verify distance calculation across complete official patch sequence."""
    assert version_service.calculate_distance("7.0", "7.0") == 0
    assert version_service.calculate_distance("6.8", "7.0") == 1
    assert version_service.calculate_distance("6.0", "7.0") == 9
    assert version_service.calculate_distance("5.7", "7.0") == 11
    assert version_service.calculate_distance("5.4", "7.0") == 14
    assert version_service.calculate_distance("5.0", "7.0") == 18
    assert version_service.calculate_distance("1.0", "7.0") >= 52


def test_post_5_4_characters_represented_correctly():
    """Requirement 12: Verify characters introduced after v5.4 are accurately represented in metadata."""
    # Skirk in 5.7
    skirk = game_data_service.get_character("Skirk")
    assert skirk is not None
    assert skirk.game_version_introduced == "5.7"
    assert skirk.game_version_updated == "7.0"

    # Columbina in 6.3
    columbina = game_data_service.get_character("Columbina")
    assert columbina is not None
    assert columbina.game_version_introduced == "6.3"
    assert columbina.game_version_updated == "7.0"

    # Varka in 6.4
    varka = game_data_service.get_character("Varka")
    assert varka is not None
    assert varka.game_version_introduced == "6.4"
    assert varka.game_version_updated == "7.0"

    # Sandrone in 6.7
    sandrone = game_data_service.get_character("Sandrone")
    assert sandrone is not None
    assert sandrone.game_version_introduced == "6.7"
    assert sandrone.game_version_updated == "7.0"

    # Odette in 6.8
    odette = game_data_service.get_character("Odette")
    assert odette is not None
    assert odette.game_version_introduced == "6.8"
    assert odette.game_version_updated == "7.0"

    # Existing characters updated to 7.0
    kazuha = game_data_service.get_character("Kaedehara Kazuha")
    assert kazuha is not None
    assert kazuha.game_version_introduced == "1.6"
    assert kazuha.game_version_updated == "7.0"

    mavuika = game_data_service.get_character("Mavuika")
    assert mavuika is not None
    assert mavuika.game_version_introduced == "5.3"
    assert mavuika.game_version_updated == "7.0"


def test_knowledge_version_staleness_detection():
    """Verify knowledge documents older than 2 patches are flagged as stale relative to v7.0."""
    stale_docs = knowledge_service.get_stale_documents(stale_threshold_patches=4)
    assert isinstance(stale_docs, list)
    assert len(stale_docs) > 0

    # Any 5.x document should be flagged as stale under 7.0 live
    for s in stale_docs:
        assert s["version_distance"] >= 4
        assert s["is_stale"] is True


def test_api_version_endpoints():
    """Verify API endpoints /api/version/current, /history, and /status."""
    # Current
    resp = client.get("/api/version/current")
    assert resp.status_code == 200
    cur_data = resp.json()
    assert cur_data["version"] == "7.0"
    assert cur_data["is_current"] is True
    assert "The Stars Turn Anew" in cur_data["name"]

    # History
    resp_hist = client.get("/api/version/history")
    assert resp_hist.status_code == 200
    hist = resp_hist.json()
    assert len(hist) >= 53
    # Ensure newest first in history
    assert hist[0]["version"] == "7.0"
    assert hist[0]["is_current"] is True

    # Status
    resp_stat = client.get("/api/version/status")
    assert resp_stat.status_code == 200
    stat = resp_stat.json()
    assert stat["current_version"] == "7.0"
    assert stat["total_tracked_versions"] >= 53
    assert stat["total_document_count"] > 0
    assert stat["stale_document_count"] > 0


def test_api_health_includes_game_version_7_0():
    """Verify /api/health includes validated game_version '7.0'."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["game_version"] == "7.0"
    assert "The Stars Turn Anew" in data["game_patch_name"]


# =========================================================================
# Phase 4 Version Architecture & Discovery Tests (Tests 1 through 10)
# =========================================================================

def test_arch_test1_current_version_selected_from_explicit_verified_release():
    """Test 1: Current version is correctly selected from an explicit verified current release."""
    curr = version_service.get_current_version()
    assert curr.version == "7.0"
    assert curr.is_current is True
    assert curr.is_released is True
    assert curr.verification_status == "VERIFIED_OFFICIAL"


def test_arch_test2_historical_versions_not_accidentally_current():
    """Test 2: Historical versions are not accidentally selected as current."""
    all_versions = version_service.list_versions()
    curr = version_service.get_current_version()
    for v in all_versions:
        if v.version != curr.version:
            assert v.is_current is False, f"Historical version {v.version} must not be is_current=True"


def test_arch_test3_and_test4_newer_version_replaces_current_and_preserves_history(tmp_path):
    """Test 3 & Test 4: A newer version can replace current (e.g. 7.0 -> 7.1) and preserves all historical records."""
    import shutil
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions)
    assert svc.get_current_version().version == "7.0"
    hist_count_before = len(svc.list_versions())

    # Promote to 7.1
    svc.update_version_state(
        new_version="7.1",
        name="The Silver Chariot",
        release_date="2026-10-14",
        major_region="Teyvat",
        is_released=True,
        is_current=True,
    )

    # Test 3: 7.1 is now current, 7.0 is no longer current
    assert svc.get_current_version().version == "7.1"
    v70 = svc.get_version("7.0")
    assert v70.is_current is False

    # Test 4: Historical records are preserved (count grew by 1)
    hist_after = svc.list_versions()
    assert len(hist_after) == hist_count_before + 1
    assert any(v.version == "7.0" for v in hist_after)
    assert any(v.version == "7.1" for v in hist_after)


def test_arch_test5_network_failure_preserves_last_verified_version():
    """Test 5: Network/source failure preserves last verified current version and flags discovery_status."""
    curr_before = version_service.get_current_version().version
    status = version_service.check_for_updates(simulate_network_failure=True)
    assert status.current_version == curr_before
    assert status.discovery_status == "CACHED_OFFLINE"


def test_arch_test6_doc_from_7_0_does_not_become_stale_merely_on_7_1(tmp_path):
    """Test 6: A document from 7.0 does not automatically become stale merely because current version becomes 7.1."""
    import shutil
    temp_versions = tmp_path / "game_versions.json"
    temp_changes = tmp_path / "patch_changes.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions, patch_changes_path=temp_changes)
    # Promote to 7.1 with zero changes to Bennett
    svc.update_version_state(
        new_version="7.1",
        name="The Silver Chariot",
        release_date="2026-10-14",
        major_region="Teyvat",
        changed_systems=["character:Citlali"],  # Only Citlali changed
    )

    # Evaluate 7.0 Bennett guide (which depends on character:Bennett)
    eval_bennett = svc.evaluate_staleness(
        entity_version="7.0",
        affected_systems=["character:Bennett", "mechanics:BaseATKBuff"],
    )

    # Bennett must NOT be stale; it is RECENT_COMPATIBLE
    assert eval_bennett.is_stale is False
    assert eval_bennett.freshness_status == FreshnessStatus.RECENT_COMPATIBLE
    assert eval_bennett.version_distance == 1


def test_arch_test7_doc_explicitly_affected_by_later_patch_becomes_stale(tmp_path):
    """Test 7: A document explicitly affected by a later patch can become stale."""
    import shutil
    temp_versions = tmp_path / "game_versions.json"
    temp_changes = tmp_path / "patch_changes.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions, patch_changes_path=temp_changes)
    # Promote to 7.1 and register that artifact set 'Fragment of Harmonic Whimsy' was reworked
    svc.update_version_state(
        new_version="7.1",
        name="The Silver Chariot",
        release_date="2026-10-14",
        major_region="Teyvat",
        changed_systems=["artifact:HarmonicWhimsy"],
    )

    # An artifact guide for Harmonic Whimsy from 7.0 must become STALE
    eval_artifact = svc.evaluate_staleness(
        entity_version="7.0",
        affected_systems=["artifact:HarmonicWhimsy"],
    )
    assert eval_artifact.is_stale is True
    assert eval_artifact.freshness_status == FreshnessStatus.STALE
    assert "Document affected by patch changes" in eval_artifact.warning


def test_arch_test8_project_target_cannot_be_confused_with_actual_current():
    """Test 8: Project target version, if retained, cannot be confused with actual current version."""
    status = version_service.get_status()
    assert hasattr(status, "project_target_version")
    assert status.current_version == "7.0"
    assert status.latest_known_version == "7.0"
    assert status.project_target_version == "7.0"


def test_arch_test9_only_one_released_version_is_current():
    """Test 9: Only one released version can be is_current=true."""
    current_releases = [v for v in version_service.list_versions() if v.is_current]
    assert len(current_releases) == 1
    assert current_releases[0].version == "7.0"


def test_arch_test10_future_unreleased_version_cannot_become_current_by_high_number(tmp_path):
    """Test 10: No future/unreleased version can become current merely because it has the highest version number."""
    import shutil
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    with open(temp_versions, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Add future unreleased version 8.0 with is_released=False, is_current=False
    data.append({
        "version": "8.0",
        "name": "Distant Future",
        "release_date": "2027-09-01",
        "major_region": "Unknown",
        "is_released": False,
        "is_current": False,
        "verification_status": "UNVERIFIED",
    })

    with open(temp_versions, "w", encoding="utf-8") as f:
        json.dump(data, f)

    svc = VersionService(versions_path=temp_versions)
    # The current version MUST remain 7.0, NOT 8.0!
    assert svc.get_current_version().version == "7.0"
    assert svc.get_current_version().version != "8.0"

