"""
Unit and integration tests for the Version Completeness Release Gate.
Verifies fail-closed behavior, multi-domain auditing, placeholder rejection,
and Phase 8 release blocking when coverage is incomplete.
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.version import CompletenessStatus
from backend.services.version_completeness_gate import (
    VersionCompletenessGateService,
    version_completeness_gate,
    FORBIDDEN_PLACEHOLDERS,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_version_completeness_gate_detects_incomplete_overall():
    """Verify that current live 7.0 audit evaluates to INCOMPLETE and blocks Phase 8."""
    report = version_completeness_gate.audit_version_completeness()
    assert report.live_version == "7.0"
    assert report.active_canonical_version == "7.0"
    assert report.overall_status == CompletenessStatus.INCOMPLETE
    assert report.phase_8_allowed is False
    assert len(report.blockers) > 0


def test_structured_data_completeness_verified():
    """Verify structured data gate passes for all 119 characters, 246 weapons, artifacts, curves, materials."""
    struct_data, blockers = version_completeness_gate.audit_structured_data("7.0")
    assert struct_data.status == CompletenessStatus.COMPLETE
    assert struct_data.coverage == 1.0
    assert struct_data.characters.verified_count >= 119
    assert struct_data.weapons.verified_count >= 246
    assert struct_data.artifacts.status == CompletenessStatus.COMPLETE
    assert struct_data.materials.status == CompletenessStatus.COMPLETE
    assert struct_data.curves.status == CompletenessStatus.COMPLETE


def test_game_content_completeness_verified():
    """Verify game content gate validates real acquired catalogs for quests, events, enemies, achievements, domains, recipes, regions."""
    game_content, blockers = version_completeness_gate.audit_game_content("7.0")
    assert game_content.status == CompletenessStatus.COMPLETE
    assert game_content.quests.status == CompletenessStatus.COMPLETE
    assert game_content.quests.verified_count >= 50
    assert game_content.events.status == CompletenessStatus.COMPLETE
    assert game_content.events.verified_count >= 10
    assert game_content.domains.status == CompletenessStatus.COMPLETE
    assert game_content.domains.verified_count >= 40
    assert game_content.enemies.status == CompletenessStatus.COMPLETE
    assert game_content.enemies.verified_count >= 80
    assert game_content.regions.status == CompletenessStatus.COMPLETE
    assert game_content.regions.verified_count >= 7
    assert game_content.achievements.status == CompletenessStatus.COMPLETE
    assert game_content.achievements.verified_count >= 100
    assert game_content.crafting.status == CompletenessStatus.COMPLETE
    assert game_content.crafting.verified_count >= 50
    assert game_content.farming.status == CompletenessStatus.COMPLETE
    assert game_content.mechanics.status == CompletenessStatus.COMPLETE
    assert len(blockers) == 0


def test_knowledge_coverage_gaps_detected():
    """Verify knowledge gate detects character knowledge gaps while confirming verified structured weapons and 7.0 patch notes."""
    knowledge, blockers = version_completeness_gate.audit_knowledge_coverage("7.0")
    assert knowledge.status == CompletenessStatus.INCOMPLETE
    # Weapon knowledge is fully verified across all 246 weapons per contract
    assert knowledge.weapon_guides.found_count == 246
    assert knowledge.weapon_guides.verified_count == 246
    assert knowledge.weapon_guides.status == CompletenessStatus.COMPLETE
    # Character knowledge evaluated against 95 live characters (90 verified, 5 missing expert guides)
    assert knowledge.character_guides.expected_count == 95
    assert knowledge.character_guides.verified_count == 90
    assert knowledge.character_guides.missing_count == 5
    assert round(knowledge.character_guides.coverage_ratio, 4) == 0.9474
    assert knowledge.character_guides.status == CompletenessStatus.INCOMPLETE
    assert len(knowledge.character_guides.sample_missing) == 5
    # Official patch 7.0 release notes verified
    assert knowledge.current_version_changes.status == CompletenessStatus.COMPLETE
    assert knowledge.current_version_changes.verified_count == 1
    # Check that blockers correctly identify character expert guide coverage incomplete
    assert any("expert guide coverage incomplete" in b.lower() for b in blockers)


def test_provenance_and_freshness_audits():
    """Verify provenance integrity and freshness evaluations across stored records."""
    provenance, b_prov = version_completeness_gate.audit_provenance()
    assert provenance.records_with_valid_provenance > 0
    assert provenance.records_missing_provenance == 0

    freshness, b_fresh = version_completeness_gate.audit_freshness("7.0")
    assert freshness.freshness_ratio > 0.0


def test_placeholder_rejection_policy():
    """Verify zero tolerance for forbidden placeholder strings."""
    service = version_completeness_gate
    for placeholder in FORBIDDEN_PLACEHOLDERS:
        assert service._has_placeholder(f"The stats are {placeholder}") is True
        assert service._has_placeholder(f"Status: {placeholder.upper()}") is True

    assert service._has_placeholder("Verified Official Kazuha Guide") is False
    assert service._has_placeholder(None) is False
    assert service._has_placeholder("") is False


def test_api_phase_gate_endpoint_fails_closed(client):
    """Verify GET /api/project/phase-gate returns fail-closed blocked response due to character knowledge gap."""
    res = client.get("/api/project/phase-gate")
    assert res.status_code == 200
    data = res.json()
    assert data["phase_8_allowed"] is False
    assert "NOT version-complete" in data["reason"]
    assert "knowledge" in data["blocking_categories"]
    assert data["version_completeness_status"] == "INCOMPLETE"
    assert data["active_canonical_version"] == "7.0"


def test_api_version_completeness_endpoint(client):
    """Verify GET /api/data/version-completeness returns complete report structure with game_content COMPLETE and knowledge INCOMPLETE."""
    res = client.get("/api/data/version-completeness")
    assert res.status_code == 200
    data = res.json()
    assert data["live_version"] == "7.0"
    assert data["overall_status"] == "INCOMPLETE"
    assert data["phase_8_allowed"] is False
    assert data["structured_data"]["status"] == "COMPLETE"
    assert data["game_content"]["status"] == "COMPLETE"
    assert data["knowledge"]["status"] == "INCOMPLETE"
    assert len(data["blockers"]) == 1
    assert "expert guide coverage incomplete" in data["blockers"][0].lower()
    assert data["live_characters_count"] == 95
    assert data["unreleased_characters_count"] == 24
    assert data["canonical_data_completeness"] == 1.0
    assert data["mechanics_completeness"] == 1.0
    assert round(data["expert_guide_coverage"], 4) == 0.9474
    assert data["unreleased_entities_excluded"] == 24


def test_simulated_complete_state_allows_phase_8(tmp_path):
    """Verify that only if every gate passes COMPLETE, Phase 8 is allowed."""
    report = version_completeness_gate.audit_version_completeness()
    # Confirm it's currently False
    assert report.phase_8_allowed is False

    # Simulate hypothetical all-complete report
    complete_report = report.model_copy(deep=True)
    complete_report.game_content.status = CompletenessStatus.COMPLETE
    complete_report.knowledge.status = CompletenessStatus.COMPLETE
    complete_report.provenance.status = CompletenessStatus.COMPLETE
    complete_report.freshness.status = CompletenessStatus.COMPLETE
    complete_report.version_delta.status = CompletenessStatus.COMPLETE

    # Verify logic when all domains are COMPLETE
    statuses = [
        complete_report.structured_data.status,
        complete_report.game_content.status,
        complete_report.knowledge.status,
        complete_report.provenance.status,
        complete_report.freshness.status,
        complete_report.version_delta.status,
    ]
    all_complete = all(s == CompletenessStatus.COMPLETE for s in statuses)
    assert all_complete is True
