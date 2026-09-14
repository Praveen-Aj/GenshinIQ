"""Unit and scenario tests for GenshinIQ Version Discovery & Verification Pipeline.

Tests all controlled scenarios (A through H) using mock discovery fixtures:
- Scenario A: Official source reports 7.0 -> remains 7.0.
- Scenario B: Official source reports 7.1 as released -> promotes to 7.1, preserves history.
- Scenario C: Official source reports upcoming 7.2 -> does NOT promote 7.2.
- Scenario D: Official source unavailable -> retains last verified version (7.0).
- Scenario E: Malformed source response -> retains last verified version.
- Scenario F: 7.0 document + 7.1 patch with unrelated changes -> document remains compatible.
- Scenario G: 7.0 document + 7.1 patch affecting its affected_systems -> document becomes stale.
- Scenario H: Repository contains a future unreleased version with higher number -> cannot become current.
"""

import json
import shutil
from pathlib import Path
import pytest

from backend.models.version import (
    DiscoveredVersionCandidate,
    FreshnessStatus,
    VerificationStatus,
)
from backend.services.version_discovery import (
    MockDiscoveryProvider,
    verify_candidate,
)
from backend.services.version_service import (
    VersionService,
    VERSIONS_FILE,
    PATCH_CHANGES_FILE,
    version_service,
)


def test_scenario_a_official_reports_same_version(tmp_path):
    """Scenario A: Official source reports 7.0 -> remains 7.0, update_available = False."""
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions)
    assert svc.get_current_version().version == "7.0"

    mock_provider = MockDiscoveryProvider(
        candidate=DiscoveredVersionCandidate(
            version="7.0",
            name="The Stars Turn Anew",
            release_date="2026-09-02",
            is_released=True,
            is_upcoming=False,
            source_id="src_hoyoverse_patch_notes",
            source_url="https://genshin.hoyoverse.com/en/news",
            raw_evidence="Version 7.0 Update Details",
        )
    )

    result = svc.check_and_update(discovery_provider=mock_provider, auto_promote=True)
    assert result.current_version == "7.0"
    assert result.discovered_version == "7.0"
    assert result.verification_status == "PASS"
    assert result.update_available is False
    assert result.promoted is False
    assert result.effective_current_version == "7.0"
    assert svc.get_current_version().version == "7.0"


def test_scenario_b_official_reports_7_1_released(tmp_path):
    """Scenario B: Official source reports 7.1 as released -> promotes 7.1, preserves history."""
    temp_versions = tmp_path / "game_versions.json"
    temp_changes = tmp_path / "patch_changes.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions, patch_changes_path=temp_changes)
    hist_before = len(svc.list_versions())

    mock_provider = MockDiscoveryProvider(
        candidate=DiscoveredVersionCandidate(
            version="7.1",
            name="The Silver Chariot",
            release_date="2026-10-14",
            is_released=True,
            is_upcoming=False,
            source_id="src_hoyoverse_patch_notes",
            source_url="https://genshin.hoyoverse.com/en/news",
            raw_evidence="Version 7.1 'The Silver Chariot' Update Details - Now Live",
            changed_systems=["character:Citlali"],
        )
    )

    result = svc.check_and_update(discovery_provider=mock_provider, auto_promote=True)
    assert result.verification_status == "PASS"
    assert result.update_available is True
    assert result.promoted is True
    assert result.effective_current_version == "7.1"

    # Verify registry state
    curr = svc.get_current_version()
    assert curr.version == "7.1"
    assert curr.is_current is True
    assert curr.is_released is True

    # 7.0 is no longer current
    v70 = svc.get_version("7.0")
    assert v70.is_current is False

    # Historical records are strictly preserved
    hist_after = svc.list_versions()
    assert len(hist_after) == hist_before + 1
    assert any(v.version == "7.0" for v in hist_after)
    assert any(v.version == "7.1" for v in hist_after)


def test_scenario_c_official_reports_upcoming_7_2(tmp_path):
    """Scenario C: Official source reports upcoming 7.2 preview -> does NOT promote 7.2."""
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions)
    assert svc.get_current_version().version == "7.0"

    mock_provider = MockDiscoveryProvider(
        candidate=DiscoveredVersionCandidate(
            version="7.2",
            name="Future Dawn",
            release_date="2026-11-25",
            is_released=False,
            is_upcoming=True,
            source_id="src_hoyoverse_patch_notes",
            source_url="https://genshin.hoyoverse.com/en/news",
            raw_evidence="Version 7.2 Special Program & Pre-installation Announcement",
        )
    )

    result = svc.check_and_update(discovery_provider=mock_provider, auto_promote=True)
    assert result.verification_status == "REJECTED_UNRELEASED"
    assert result.update_available is False
    assert result.promoted is False
    assert result.effective_current_version == "7.0"
    assert svc.get_current_version().version == "7.0"


def test_scenario_d_official_source_unavailable(tmp_path):
    """Scenario D: Official source unavailable -> retains last verified version."""
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions)
    mock_provider = MockDiscoveryProvider(simulate_network_failure=True)

    result = svc.check_and_update(discovery_provider=mock_provider, auto_promote=True)
    assert result.verification_status == "FAILED"
    assert result.discovery_status == "CACHED_OFFLINE"
    assert result.effective_current_version == "7.0"
    assert svc.get_current_version().version == "7.0"


def test_scenario_e_malformed_source_response(tmp_path):
    """Scenario E: Malformed source response -> retains last verified version."""
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions)
    mock_provider = MockDiscoveryProvider(simulate_malformed=True)

    result = svc.check_and_update(discovery_provider=mock_provider, auto_promote=True)
    assert result.verification_status == "FAILED"
    assert result.discovery_status == "MALFORMED_DATA"
    assert result.effective_current_version == "7.0"
    assert svc.get_current_version().version == "7.0"


def test_scenario_f_doc_7_0_compatible_with_7_1_unrelated_changes(tmp_path):
    """Scenario F: 7.0 document + 7.1 patch with unrelated changes -> document remains RECENT_COMPATIBLE."""
    temp_versions = tmp_path / "game_versions.json"
    temp_changes = tmp_path / "patch_changes.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions, patch_changes_path=temp_changes)

    # Promote to 7.1 where only Citlali was changed
    svc.update_version_state(
        new_version="7.1",
        name="The Silver Chariot",
        release_date="2026-10-14",
        major_region="Teyvat",
        changed_systems=["character:Citlali"],
    )

    # Bennett 7.0 guide
    eval_bennett = svc.evaluate_staleness(
        entity_version="7.0",
        affected_systems=["character:Bennett", "mechanics:BaseATKBuff"],
    )
    assert eval_bennett.freshness_status == FreshnessStatus.RECENT_COMPATIBLE
    assert eval_bennett.is_stale is False
    assert eval_bennett.version_distance == 1


def test_scenario_g_doc_7_0_stale_when_affected_system_changed(tmp_path):
    """Scenario G: 7.0 document + 7.1 patch affecting its affected_systems -> document becomes STALE."""
    temp_versions = tmp_path / "game_versions.json"
    temp_changes = tmp_path / "patch_changes.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    svc = VersionService(versions_path=temp_versions, patch_changes_path=temp_changes)

    # Promote to 7.1 with rework to artifact set Fragment of Harmonic Whimsy
    svc.update_version_state(
        new_version="7.1",
        name="The Silver Chariot",
        release_date="2026-10-14",
        major_region="Teyvat",
        changed_systems=["artifact:HarmonicWhimsy"],
    )

    # Harmonic Whimsy guide from 7.0
    eval_artifact = svc.evaluate_staleness(
        entity_version="7.0",
        affected_systems=["artifact:HarmonicWhimsy"],
    )
    assert eval_artifact.freshness_status == FreshnessStatus.STALE
    assert eval_artifact.is_stale is True
    assert "affected by patch changes" in eval_artifact.warning.lower()


def test_scenario_h_future_unreleased_version_cannot_become_current(tmp_path):
    """Scenario H: Repository contains a future version with higher number -> cannot become current."""
    temp_versions = tmp_path / "game_versions.json"
    shutil.copy(VERSIONS_FILE, temp_versions)

    with open(temp_versions, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Inject unreleased future patch 8.0 into registry JSON
    data.append({
        "version": "8.0",
        "name": "Distant Era",
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
    curr = svc.get_current_version()
    assert curr.version == "7.0"
    assert curr.version != "8.0"


def test_version_registry_integrity_invariants():
    """Requirement 11: Enforce registry invariants on canonical game_versions.json."""
    all_versions = version_service.list_versions()
    current_versions = [v for v in all_versions if v.is_current]

    # Invariant 1: Exactly one released version is_current=True
    assert len(current_versions) == 1
    assert current_versions[0].is_released is True
    assert current_versions[0].verification_status == VerificationStatus.VERIFIED_OFFICIAL.value

    # Invariant 2: At most one is_project_target=True
    target_versions = [v for v in all_versions if v.is_project_target]
    assert len(target_versions) <= 1

    # Invariant 3: No unreleased version is current
    unreleased = [v for v in all_versions if not v.is_released]
    for u in unreleased:
        assert u.is_current is False

    # Invariant 4: Historical version count is at least 53 patches
    assert len(all_versions) >= 53
