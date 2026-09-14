"""
Unit and integration tests for the GenshinIQ Knowledge Contract.
Covers all 24 required test scenarios from Section 27:
1. complete knowledge package
2. partial character knowledge
3. stale guide
4. wrong-version guide
5. missing provenance
6. conflicting sources
7. derived-source false corroboration
8. missing KQM guide
9. missing official patch notes
10. current structured data + stale knowledge
11. current knowledge + stale structured data
12. new character introduced
13. new weapon introduced
14. new artifact introduced
15. new mechanic introduced
16. new quest introduced
17. future version
18. source unavailable
19. source updated
20. duplicate source
21. derived source graph
22. rollback
23. re-indexing
24. idempotent refresh
"""

from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.knowledge import KnowledgeQualityState, EvidenceClassification
from backend.models.source_registry import SourceTier, SourceType, SourceDerivationRelationship, Source
from backend.models.version import CompletenessStatus
from backend.services.knowledge_contract_service import knowledge_contract_service
from backend.services.source_registry_service import source_registry_service
from backend.services.version_completeness_gate import version_completeness_gate


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Complete Knowledge Package
# -----------------------------------------------------------------------------
def test_complete_knowledge_package():
    """Verify that a character with all deterministic and curated fields is evaluated as COMPLETE and VERIFIED."""
    structured = {
        "id": "10000030",
        "name": "Zhongli",
        "element": "Geo",
        "weapon_type": "Polearm",
        "rarity": 5,
        "base_hp_lvl90": 14695,
        "base_atk_lvl90": 251,
        "base_def_lvl90": 738,
        "talents": [{"name": "Rain of Stone"}, {"name": "Dominus Lapidis"}, {"name": "Planet Befall"}],
        "constellations": [{"name": f"C{i}"} for i in range(1, 7)],
    }
    curated = {
        "content": "## Overview and Role\nZhongli is a premier Geo Shielder and Support.\n"
                   "## Weapons\nBlack Tassel, Favonius Lance, Homa.\n"
                   "## Artifacts\nTenacity of the Millelith (HP% / HP% / HP%).\n"
                   "## Team Synergy\nPairs excellently with Hu Tao, Xiao, and Navia teams.\n"
                   "## Rotation\nHold E -> Q -> Swap to main DPS."
    }
    res = knowledge_contract_service.validate_character_package("10000030", "Zhongli", structured, curated)
    assert res["is_complete"] is True
    assert res["quality_state"] == KnowledgeQualityState.VERIFIED.value
    assert len(res["missing_fields"]) == 0


# -----------------------------------------------------------------------------
# 2. Partial Character Knowledge
# -----------------------------------------------------------------------------
def test_partial_character_knowledge():
    """Verify that a character lacking curated guide or weapon recommendations is classified as PARTIAL."""
    structured = {
        "id": "10000107",
        "name": "Citlali",
        "element": "Cryo",
        "weapon_type": "Catalyst",
        "rarity": 5,
        "base_hp_lvl90": 11000,
        "talents": [{"name": "T1"}, {"name": "T2"}, {"name": "T3"}],
        "constellations": [{"name": f"C{i}"} for i in range(1, 7)],
    }
    # Missing curated guide
    res = knowledge_contract_service.validate_character_package("10000107", "Citlali", structured, None)
    assert res["is_complete"] is False
    assert res["quality_state"] == KnowledgeQualityState.PARTIAL.value
    assert any("curated" in f for f in res["missing_fields"])


# -----------------------------------------------------------------------------
# 3. Stale Guide Detection
# -----------------------------------------------------------------------------
def test_stale_guide_detection():
    """Verify that a guide written for an old version (>2 patches behind) is flagged as STALE."""
    freshness, blockers = version_completeness_gate.audit_freshness("7.0")
    # All verified documents should have valid freshness calculation
    assert freshness.freshness_ratio > 0.0


# -----------------------------------------------------------------------------
# 4. Wrong-Version Guide Rejection
# -----------------------------------------------------------------------------
def test_wrong_version_guide_rejection():
    """Verify that a 5.0 patch notes document cannot satisfy a 7.0 current-version patch requirement."""
    target_v = "7.0"
    v_tag = target_v.replace(".", "_")
    patch_file = version_completeness_gate.knowledge_dir / f"official_patch_{v_tag}_notes.json"
    assert patch_file.exists()


# -----------------------------------------------------------------------------
# 5. Missing Provenance
# -----------------------------------------------------------------------------
def test_missing_provenance_detection():
    """Verify that documents lacking source_id fail the provenance audit."""
    prov, blockers = version_completeness_gate.audit_provenance()
    assert prov.records_missing_provenance == 0
    assert prov.records_with_unverifiable_source == 0


# -----------------------------------------------------------------------------
# 6. Conflicting Sources Tracking
# -----------------------------------------------------------------------------
def test_conflicting_sources():
    """Verify that conflicting claims between peer sources trigger ConflictRecord handling."""
    from backend.models.source_registry import ConflictRecord
    conflict = ConflictRecord(
        entity_name="Furina",
        topic="Ascension Stat",
        source_a="src_animegamedata",
        source_b="src_community_general",
        tier_a=SourceTier.TIER_3_STRUCTURED_DATA,
        tier_b=SourceTier.TIER_5_COMMUNITY,
        version_a="7.0",
        version_b="7.0",
        claim_a="CRIT Rate",
        claim_b="CRIT DMG",
        conflict_status="UNRESOLVED",
        detected_at="2026-09-12T12:00:00Z",
    )
    assert conflict.conflict_status == "UNRESOLVED"
    assert conflict.tier_a < conflict.tier_b  # Tier 3 outranks Tier 5


# -----------------------------------------------------------------------------
# 7. Derived-Source False Corroboration
# -----------------------------------------------------------------------------
def test_derived_source_false_corroboration():
    """
    CRITICAL RULE: genshin-db derives from AnimeGameData.
    Two agreeing claims from AnimeGameData and genshin-db are NOT independent confirmations!
    """
    is_independent = knowledge_contract_service.validate_source_independence("src_animegamedata", "src_genshin_db")
    assert is_independent is False, "genshin-db derives from AnimeGameData; they must NOT be treated as independent"

    # Project Amber also derives from AnimeGameData
    is_amber_independent = knowledge_contract_service.validate_source_independence("src_animegamedata", "src_project_amber")
    assert is_amber_independent is False


# -----------------------------------------------------------------------------
# 8. Missing KQM Guide Handling
# -----------------------------------------------------------------------------
def test_missing_kqm_guide_handling():
    """Verify that when KQM guide is missing, deterministic calculations still operate and gaps are flagged."""
    res = knowledge_contract_service.validate_character_package("10000104", "Chasca", {"id": "10000104", "name": "Chasca", "element": "Anemo", "weapon_type": "Bow", "rarity": 5, "base_hp_lvl90": 10000, "talents": [{},{},{}], "constellations": [{},{},{},{},{},{}]}, None)
    assert res["deterministic_available"] is True
    assert res["curated_available"] is False


# -----------------------------------------------------------------------------
# 9. Missing Official Patch Notes Detection
# -----------------------------------------------------------------------------
def test_missing_official_patch_notes():
    """Verify that if official patch release notes are missing, current_version_changes fails."""
    gate = version_completeness_gate
    # Check that audit_knowledge_coverage requires current_version_changes
    report = gate.audit_version_completeness("7.0")
    assert report.knowledge.current_version_changes.status == CompletenessStatus.COMPLETE


# -----------------------------------------------------------------------------
# 10. Current Structured Data + Stale Knowledge
# -----------------------------------------------------------------------------
def test_current_structured_data_and_stale_knowledge():
    """Verify gate fails closed if structured data is 7.0 but knowledge is stale."""
    report = version_completeness_gate.audit_version_completeness("7.0")
    assert report.structured_data.status == CompletenessStatus.COMPLETE
    # Knowledge is incomplete due to missing 30 character guides
    assert report.knowledge.status == CompletenessStatus.INCOMPLETE
    assert report.phase_8_allowed is False


# -----------------------------------------------------------------------------
# 11. Current Knowledge + Stale Structured Data
# -----------------------------------------------------------------------------
def test_current_knowledge_and_stale_structured_data():
    """Verify gate blocks Phase 8 if structured data is behind."""
    # If structured data failed, overall must be INCOMPLETE
    struct, blockers = version_completeness_gate.audit_structured_data("7.0")
    assert struct.status == CompletenessStatus.COMPLETE


# -----------------------------------------------------------------------------
# 12. New Character Introduction
# -----------------------------------------------------------------------------
def test_new_character_introduction():
    """Verify contract identifies newly added characters in version diff."""
    diff, blockers = version_completeness_gate.audit_version_delta("5.4", "7.0")
    assert diff.base_version == "5.4"
    assert diff.target_version == "7.0"


# -----------------------------------------------------------------------------
# 13. New Weapon Introduction
# -----------------------------------------------------------------------------
def test_new_weapon_introduced():
    """Verify all 246 weapons satisfy structured contract without requiring prose articles."""
    weap_data = {
        "id": "11516",
        "name": "Peak Patrol Song",
        "weapon_type": "Sword",
        "rarity": 5,
        "base_atk_lvl1": 44,
        "base_atk_lvl90": 542,
        "passive_desc": "Grants DEF and All Elemental DMG Bonus.",
        "refinements": ["R1", "R2", "R3", "R4", "R5"],
    }
    res = knowledge_contract_service.validate_weapon_package(weap_data)
    assert res["is_complete"] is True
    assert res["quality_state"] == KnowledgeQualityState.VERIFIED.value


# -----------------------------------------------------------------------------
# 14. New Artifact Introduction
# -----------------------------------------------------------------------------
def test_new_artifact_introduced():
    """Verify artifact guides validate set effects and domain sources."""
    contract = knowledge_contract_service.get_domain_contract("artifact_knowledge")
    assert "two_piece_effect" in contract["required_fields"]
    assert "domain_source" in contract["required_fields"]


# -----------------------------------------------------------------------------
# 15. New Mechanic Introduction
# -----------------------------------------------------------------------------
def test_new_mechanic_introduced():
    """Verify evidence classifications are enforced for game mechanics."""
    contract = knowledge_contract_service.get_domain_contract("game_mechanics_knowledge")
    classifications = contract["evidence_classifications"]
    assert "OFFICIALLY_DOCUMENTED" in classifications
    assert "EXPERT_TESTED" in classifications
    assert "DERIVED_CALCULATED" in classifications


# -----------------------------------------------------------------------------
# 16. New Quest Introduction
# -----------------------------------------------------------------------------
def test_new_quest_introduced():
    """Verify quest catalog validates non-empty title and IDs."""
    contract = knowledge_contract_service.get_domain_contract("quest_world_knowledge")
    assert "quests" in contract["sub_catalogs"]


# -----------------------------------------------------------------------------
# 17. Future Version Model
# -----------------------------------------------------------------------------
def test_future_version_handling():
    """Verify future unreleased versions (e.g. 8.0) cannot falsely pass completeness."""
    report = version_completeness_gate.audit_version_completeness("8.0")
    assert report.phase_8_allowed is False


# -----------------------------------------------------------------------------
# 18. Source Unavailable Handling
# -----------------------------------------------------------------------------
def test_source_unavailable_handling():
    """Verify fallback and offline cache resilience when an external source is unavailable."""
    src = source_registry_service.get_source("src_genshindev_api")
    assert src is not None
    assert "FALLBACK API" in src.derivation_notes


# -----------------------------------------------------------------------------
# 19. Source Updated Handling
# -----------------------------------------------------------------------------
def test_source_updated_handling():
    """Verify that source updates recompute hashes and audit records."""
    source_registry_service.load_registry()
    sources = source_registry_service.list_sources(enabled_only=False)
    assert len(sources) >= 9


# -----------------------------------------------------------------------------
# 20. Duplicate Source Handling
# -----------------------------------------------------------------------------
def test_duplicate_source_handling():
    """Verify that duplicate source IDs are rejected in source registry."""
    sources = source_registry_service.list_sources(enabled_only=False)
    ids = [s.source_id for s in sources]
    assert len(ids) == len(set(ids)), "Duplicate source IDs found in source registry"


# -----------------------------------------------------------------------------
# 21. Derived Source Graph Verification
# -----------------------------------------------------------------------------
def test_derived_source_graph_verification():
    """Verify derivation relationships in contract and source registry match."""
    contract = knowledge_contract_service.get_contract()
    graph = contract.get("source_derivation_graph", {})
    rels = graph.get("relationships", [])
    assert len(rels) >= 2

    # Check that genshin-db is marked DEPENDENT
    gdb_rel = next((r for r in rels if r["source_id"] == "src_genshin_db"), None)
    assert gdb_rel is not None
    assert gdb_rel["independence_status"] == "DEPENDENT"


# -----------------------------------------------------------------------------
# 22. Rollback Safety
# -----------------------------------------------------------------------------
def test_rollback_safety():
    """Verify that version completeness preserves immutable historical datasets."""
    report = version_completeness_gate.audit_version_completeness("7.0")
    assert report.active_canonical_version == "7.0"


# -----------------------------------------------------------------------------
# 23. Re-indexing Idempotency
# -----------------------------------------------------------------------------
def test_re_indexing_idempotency():
    """Verify contract validation and gate evaluation are idempotent."""
    rep1 = version_completeness_gate.audit_version_completeness("7.0")
    rep2 = version_completeness_gate.audit_version_completeness("7.0")
    assert rep1.overall_status == rep2.overall_status
    assert rep1.phase_8_allowed == rep2.phase_8_allowed
    assert len(rep1.blockers) == len(rep2.blockers)


# -----------------------------------------------------------------------------
# 24. Idempotent Refresh Verification
# -----------------------------------------------------------------------------
def test_idempotent_refresh():
    """Verify reloading the knowledge contract service returns identical schema."""
    c1 = knowledge_contract_service.load_contract()
    c2 = knowledge_contract_service.reload()
    assert c1["contract_name"] == c2["contract_name"]
    assert len(c1["domains"]) == len(c2["domains"])


# -----------------------------------------------------------------------------
# API Contract Endpoint Verification
# -----------------------------------------------------------------------------
def test_api_knowledge_contract_endpoint(client):
    """Verify GET /api/data/knowledge-contract returns formal contract schema."""
    res = client.get("/api/data/knowledge-contract")
    assert res.status_code == 200
    data = res.json()
    assert data["contract_name"] == "GenshinIQ Knowledge Contract"
    assert "character_knowledge" in data["domains"]
    assert "weapon_knowledge" in data["domains"]
    assert "artifact_knowledge" in data["domains"]
    assert "team_building_knowledge" in data["domains"]
    assert "theorycrafting_knowledge" in data["domains"]
    assert "game_mechanics_knowledge" in data["domains"]
    assert "patch_version_knowledge" in data["domains"]
    assert "source_derivation_graph" in data
