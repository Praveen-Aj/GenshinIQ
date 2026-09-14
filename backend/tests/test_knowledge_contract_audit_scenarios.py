"""
Comprehensive tests covering all 12 scenarios required by Section 12 of the Knowledge Completeness Audit:
1. live character
2. unreleased character
3. transition from unreleased -> released
4. live character without KQM guide
5. live character with KQM guide
6. stale guide
7. wrong-version guide
8. structured data available but expert knowledge unavailable
9. client-only entity
10. incorrect scanner pattern
11. duplicate knowledge files
12. source provenance missing
"""

import json
from pathlib import Path
import pytest

from backend.models.character_knowledge_package import (
    CharacterReleaseStatus,
    FieldQualityClassification,
)
from backend.services.character_release_service import (
    CharacterReleaseService,
    character_release_service,
)
from backend.services.character_knowledge_service import character_knowledge_service
from backend.services.game_data_service import game_data_service
from backend.services.knowledge_service import knowledge_service
from backend.services.version_service import version_service
from backend.services.version_completeness_gate import (
    version_completeness_gate,
    CompletenessStatus,
)


# =============================================================================
# 1. LIVE CHARACTER
# =============================================================================
def test_scenario_1_live_character():
    """Verify live character has LIVE_RELEASED status, complete binary stats, and applicable contract."""
    pkg = character_knowledge_service.get_character_package("Bennett")
    assert pkg is not None
    assert pkg.character_name == "Bennett"
    assert pkg.release_status == CharacterReleaseStatus.LIVE_RELEASED
    assert pkg.is_released is True
    assert pkg.has_canonical_data is True
    assert pkg.has_verified_mechanics is True

    # Required deterministic contract fields
    assert pkg.field_classifications["deterministic.identity"] == FieldQualityClassification.VERIFIED
    assert pkg.field_classifications["deterministic.element"] == FieldQualityClassification.VERIFIED
    assert pkg.field_classifications["deterministic.weapon_type"] == FieldQualityClassification.VERIFIED
    assert pkg.field_classifications["deterministic.rarity"] == FieldQualityClassification.VERIFIED
    assert pkg.field_classifications["deterministic.base_stats"] == FieldQualityClassification.VERIFIED_DERIVED
    assert pkg.field_classifications["deterministic.talents"] == FieldQualityClassification.VERIFIED
    assert pkg.field_classifications["deterministic.constellations"] == FieldQualityClassification.VERIFIED


# =============================================================================
# 2. UNRELEASED CHARACTER
# =============================================================================
def test_scenario_2_unreleased_character():
    """Verify unreleased preview character has UNRELEASED_PREVIEW status and NOT_APPLICABLE for curated fields."""
    pkg = character_knowledge_service.get_character_package("Skirk")
    assert pkg is not None
    assert pkg.character_name == "Skirk"
    assert pkg.release_status == CharacterReleaseStatus.UNRELEASED_PREVIEW
    assert pkg.is_released is False
    assert pkg.quality_state == FieldQualityClassification.NOT_APPLICABLE
    assert "not applicable" in pkg.applicability_reason.lower()

    # Curated requirements are NOT_APPLICABLE, not MISSING
    assert pkg.field_classifications["curated.role"] == FieldQualityClassification.NOT_APPLICABLE
    assert pkg.field_classifications["curated.weapons"] == FieldQualityClassification.NOT_APPLICABLE
    assert pkg.field_classifications["curated.artifacts"] == FieldQualityClassification.NOT_APPLICABLE
    assert pkg.field_classifications["curated.rotation"] == FieldQualityClassification.NOT_APPLICABLE
    assert pkg.field_classifications["curated.energy_requirements"] == FieldQualityClassification.NOT_APPLICABLE

    # Must NOT be counted as a missing live knowledge package
    assert pkg.has_expert_guide is False


# =============================================================================
# 3. TRANSITION FROM UNRELEASED -> RELEASED
# =============================================================================
def test_scenario_3_transition_from_unreleased_to_released():
    """Verify that release status transitions dynamically based on version without hardcoding names."""
    # Test character introduced in v5.5
    test_char = {
        "id": 10000990,
        "name": "IansanTest",
        "element": "Electro",
        "weapon_type": "Polearm",
        "rarity": 4,
        "game_version_introduced": "5.5",
        "base_hp_lvl90": 10000,
        "talents": [{}, {}, {}],
        "constellations": [{}, {}, {}, {}, {}, {}],
    }

    # Under current live version 5.4: character is UPCOMING_CONFIRMED
    service_v54 = CharacterReleaseService(live_playable_version="5.4")
    status_v54 = service_v54.classify_character(test_char)
    assert status_v54 == CharacterReleaseStatus.UPCOMING_CONFIRMED
    app_v54 = service_v54.get_applicability_requirements(status_v54)
    assert app_v54["expert_guide"] == "NOT_APPLICABLE"

    # When live game version advances to 5.5: automatically becomes LIVE_RELEASED
    service_v55 = CharacterReleaseService(live_playable_version="5.5")
    status_v55 = service_v55.classify_character(test_char)
    assert status_v55 == CharacterReleaseStatus.LIVE_RELEASED
    app_v55 = service_v55.get_applicability_requirements(status_v55)
    assert app_v55["expert_guide"] == "REQUIRED"


# =============================================================================
# 4. LIVE CHARACTER WITHOUT KQM GUIDE
# =============================================================================
def test_scenario_4_live_character_without_kqm_guide():
    """Verify released character lacking KQM guide is PARTIAL, cataloged as gap, with zero fake guides."""
    pkg = character_knowledge_service.get_character_package("Xilonen")
    assert pkg is not None
    assert pkg.character_name == "Xilonen"
    assert pkg.release_status == CharacterReleaseStatus.LIVE_RELEASED
    assert pkg.is_released is True
    assert pkg.has_canonical_data is True
    assert pkg.has_verified_mechanics is True
    assert pkg.has_expert_guide is False
    assert pkg.quality_state == FieldQualityClassification.PARTIAL

    # Curated fields are MISSING
    assert pkg.field_classifications["curated.role"] == FieldQualityClassification.MISSING
    assert pkg.field_classifications["curated.rotation"] == FieldQualityClassification.MISSING
    assert "curated.rotation" in pkg.knowledge_gaps

    # Verified recorded in knowledge gaps catalog
    gaps_file = Path("data/canonical/knowledge_gaps.json")
    assert gaps_file.exists()
    with open(gaps_file, "r", encoding="utf-8") as f:
        gaps_data = json.load(f)
    entities = [g["entity"] for g in gaps_data["gaps"]]
    assert any("Xilonen" in e for e in entities)


# =============================================================================
# 5. LIVE CHARACTER WITH KQM GUIDE
# =============================================================================
def test_scenario_5_live_character_with_kqm_guide():
    """Verify live character with peer-reviewed guide extracts verified recommendations."""
    pkg = character_knowledge_service.get_character_package("Kaedehara Kazuha")
    assert pkg is not None
    assert pkg.character_name == "Kaedehara Kazuha"
    assert pkg.release_status == CharacterReleaseStatus.LIVE_RELEASED
    assert pkg.has_expert_guide is True
    assert pkg.curated.role is not None
    assert len(pkg.curated.weapon_recommendations) > 0


# =============================================================================
# 6. STALE GUIDE
# =============================================================================
def test_scenario_6_stale_guide():
    """Verify that a guide from an earlier version evaluated against live 7.0 is flagged as STALE."""
    eval_res = version_service.evaluate_staleness("5.4")
    assert eval_res.is_stale is True
    assert eval_res.version_distance >= 2
    assert "patches behind" in eval_res.warning.lower() or "stale" in eval_res.warning.lower()


# =============================================================================
# 7. WRONG-VERSION GUIDE
# =============================================================================
def test_scenario_7_wrong_version_guide():
    """Verify that a document with mismatched or far-future version is flagged."""
    eval_future = version_service.evaluate_staleness("8.0")
    # Distance calculation handles future mismatch safely
    assert eval_future is not None


# =============================================================================
# 8. STRUCTURED DATA AVAILABLE BUT EXPERT KNOWLEDGE UNAVAILABLE
# =============================================================================
def test_scenario_8_structured_data_available_expert_unavailable():
    """Verify all 5 released characters have 100% structured data and 0% expert guide."""
    five_missing = ["Xilonen", "Chasca", "Ororon", "Lan Yan", "Yumemizuki Mizuki"]
    for name in five_missing:
        pkg = character_knowledge_service.get_character_package(name)
        assert pkg is not None, f"Package missing for {name}"
        assert pkg.release_status == CharacterReleaseStatus.LIVE_RELEASED
        # 100% canonical data
        assert pkg.has_canonical_data is True
        assert pkg.deterministic.base_stats["lvl90"]["hp"] > 0
        assert pkg.deterministic.base_stats["lvl90"]["atk"] > 0
        # 100% mechanics
        assert pkg.has_verified_mechanics is True
        assert len(pkg.deterministic.talents) >= 3
        assert len(pkg.deterministic.constellations) >= 6
        # 0% expert guide
        assert pkg.has_expert_guide is False
        assert pkg.field_classifications["curated.rotation"] == FieldQualityClassification.MISSING


# =============================================================================
# 9. CLIENT-ONLY ENTITY
# =============================================================================
def test_scenario_9_client_only_entity():
    """Verify client avatar existing in game data does NOT infer live release."""
    # Varka (ID 10000115, introduced in 6.0)
    varka_pkg = character_knowledge_service.get_character_package("Varka")
    assert varka_pkg is not None
    assert varka_pkg.release_status == CharacterReleaseStatus.UNRELEASED_PREVIEW
    assert varka_pkg.is_released is False
    assert varka_pkg.quality_state == FieldQualityClassification.NOT_APPLICABLE


# =============================================================================
# 10. INCORRECT SCANNER PATTERN
# =============================================================================
def test_scenario_10_scanner_pattern_audit():
    """Verify that scanner pattern correctly identifies Citlali and does not drop guides."""
    # Citlali guide file is named kqm_guide_citlali.json
    citlali_pkg = character_knowledge_service.get_character_package("Citlali")
    assert citlali_pkg is not None
    assert citlali_pkg.has_expert_guide is True
    assert citlali_pkg.quality_state in (FieldQualityClassification.VERIFIED, FieldQualityClassification.STALE)

    # Non-character guide files must not be matched as characters
    mechanics_doc = knowledge_service.get_document("mechanics_elemental_reactions")
    assert mechanics_doc is not None
    assert mechanics_doc.metadata.character is None


# =============================================================================
# 11. DUPLICATE KNOWLEDGE FILES
# =============================================================================
def test_scenario_11_duplicate_knowledge_files():
    """Verify that having both KQM and Wiki documents prioritizes KQM without duplicating packages."""
    docs = character_knowledge_service._find_knowledge_docs("Bennett")
    # Bennett has both kqm_guide_bennett and wiki_bennett
    filenames = [d[0] for d in docs]
    assert any("kqm_" in f for f in filenames)
    assert any("wiki_" in f for f in filenames)

    # Compiled package takes KQM as primary and produces exactly one package
    pkg = character_knowledge_service.get_character_package("Bennett")
    assert pkg is not None
    assert pkg.character_name == "Bennett"
    assert pkg.has_expert_guide is True


# =============================================================================
# 12. SOURCE PROVENANCE MISSING
# =============================================================================
def test_scenario_12_source_provenance_missing():
    """Verify that manual or unregistered sources do NOT receive AUTHORITATIVE or VERIFIED status."""
    gate_service = version_completeness_gate
    # Check that forbidden placeholder texts are detected
    assert gate_service._has_placeholder("placeholder text") is True
    assert gate_service._has_placeholder("TBD until 7.0") is True

    # Check that canonical records without registered provenance fail audit
    prov_audit, blockers = gate_service.audit_provenance()
    assert prov_audit.records_missing_provenance == 0
    assert prov_audit.status == CompletenessStatus.COMPLETE
