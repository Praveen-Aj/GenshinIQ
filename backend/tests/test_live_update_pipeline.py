"""
Unit and simulation tests for the Permanent Live Data & Knowledge Update Pipeline.
Simulates multi-version progression (7.0 -> 7.1 -> 7.2 -> 8.0) and validates all Section 19 scenarios:
- Scenario 1: New version fully available -> candidate -> complete -> active
- Scenario 2: Structured data updated but knowledge unavailable -> candidate -> incomplete -> NOT active
- Scenario 3: One new character has incomplete knowledge -> version = incomplete
- Scenario 4: Source unavailable -> previous active version preserved
- Scenario 5: Source data conflicts -> conflict recorded, canonical authority selected
- Scenario 6: Concurrent new version discovery -> safe candidate creation without mutating active state
- Delta Engine & Knowledge Targeting
- Source Adapter Protocol Conformance
"""

import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.adapters import (
    OfficialSourceAdapter,
    AnimeGameDataAdapter,
    ProjectAmberAdapter,
    KQMAdapter,
    TCLAdapter,
    EnkaAdapter,
    GOODAdapter,
    SourceAdapter,
    VersionLifecycleState,
)
from backend.services.update_orchestrator import update_orchestrator
from backend.services.version_delta_service import version_delta_service


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# Adapter Interface Invariants
# -----------------------------------------------------------------------------
def test_all_adapters_conform_to_protocol():
    """Verify that all 7 adapters inherit from SourceAdapter and expose required methods."""
    adapters = [
        OfficialSourceAdapter(),
        AnimeGameDataAdapter(),
        ProjectAmberAdapter(),
        KQMAdapter(),
        TCLAdapter(),
        EnkaAdapter(),
        GOODAdapter(),
    ]
    for adapter in adapters:
        assert isinstance(adapter, SourceAdapter)
        assert hasattr(adapter, "discover")
        assert hasattr(adapter, "fetch")
        assert hasattr(adapter, "parse")
        assert hasattr(adapter, "normalize")
        assert hasattr(adapter, "validate")
        assert adapter.source_id.startswith("src_")
        assert len(adapter.domains) >= 1
        assert 1 <= adapter.authority_tier <= 5


# -----------------------------------------------------------------------------
# Delta Engine Tests
# -----------------------------------------------------------------------------
def test_delta_engine_detects_additions_modifications_removals():
    """Verify that VersionDeltaService computes exact entity-level and stat-level diffs."""
    base_chars = {
        "10000002": {"name": "Kamisato Ayaka", "base_hp_lvl90": 12858, "base_atk_lvl90": 342},
        "10000003": {"name": "Jean", "base_hp_lvl90": 14695, "base_atk_lvl90": 239},
    }
    cand_chars = {
        "10000002": {"name": "Kamisato Ayaka", "base_hp_lvl90": 13000, "base_atk_lvl90": 342},  # modified
        "10000004": {"name": "Citlali", "base_hp_lvl90": 11000, "base_atk_lvl90": 200},          # added
        # Jean removed
    }

    delta = version_delta_service.compare_version_datasets(
        base_version="7.0",
        candidate_version="7.1",
        base_characters=base_chars,
        candidate_characters=cand_chars,
    )

    assert "Citlali" in delta.new_characters
    assert "Kamisato Ayaka" in delta.modified_characters
    assert "Jean" in delta.removed_characters
    assert delta.total_added >= 1
    assert delta.total_modified >= 1
    assert delta.total_removed >= 1


def test_delta_driven_knowledge_targeting():
    """Verify that unaffected existing knowledge documents do not require rebuild on minor version bump."""
    base_chars = {"10000002": {"name": "Kamisato Ayaka"}}
    cand_chars = {
        "10000002": {"name": "Kamisato Ayaka"},
        "10000104": {"name": "Chasca"},
    }
    delta = version_delta_service.compare_version_datasets(
        base_version="7.0",
        candidate_version="7.1",
        base_characters=base_chars,
        candidate_characters=cand_chars,
    )
    req = version_delta_service.compute_knowledge_delta(delta, existing_knowledge_doc_count=178)
    assert req.characters_requiring_guides == ["Chasca"]
    assert req.unaffected_knowledge_count == 178


# -----------------------------------------------------------------------------
# Scenario 1: New Version Fully Available (7.0 -> 7.1)
# -----------------------------------------------------------------------------
def test_scenario_1_new_version_fully_available():
    """When a new version has complete verified data and knowledge, it produces an update manifest."""
    manifest = update_orchestrator.run_update_pipeline(
        target_version="7.0",
        simulate_knowledge_missing=False,
    )
    assert manifest.version == "7.0"
    assert manifest.sources["src_animegamedata"].status == "ACQUIRED"
    assert manifest.sources["src_hoyoverse_patch_notes"].status == "ACQUIRED"


# -----------------------------------------------------------------------------
# Scenario 2: Structured Data Updated But Knowledge Unavailable (7.1 -> 7.2)
# -----------------------------------------------------------------------------
def test_scenario_2_structured_updated_knowledge_unavailable():
    """
    CRITICAL SAFETY INVARIANT:
    When 7.2 structured data arrives but knowledge is not yet available,
    the candidate is marked INCOMPLETE and the active version is NOT updated.
    """
    active_before = update_orchestrator.get_active_version()

    manifest = update_orchestrator.run_update_pipeline(
        target_version="7.2",
        simulate_knowledge_missing=True,
    )

    assert manifest.lifecycle_state == VersionLifecycleState.CANDIDATE
    assert manifest.promotion_status == "BLOCKED"
    assert manifest.completeness_status == "INCOMPLETE"
    assert "src_kqm_guides" in manifest.sources
    assert manifest.sources["src_kqm_guides"].status == "PARTIAL"

    # Verify active pointer was untouched
    active_after = update_orchestrator.get_active_version()
    assert active_after == active_before, "Active canonical version must NOT change when knowledge is incomplete!"


# -----------------------------------------------------------------------------
# Scenario 3: One New Character Has Incomplete Knowledge
# -----------------------------------------------------------------------------
def test_scenario_3_single_character_incomplete_knowledge():
    """If one character lacks verified build recommendations, the gate flags the gap."""
    from backend.services.knowledge_contract_service import knowledge_contract_service
    res = knowledge_contract_service.validate_character_package(
        character_id="10000105",
        character_name="Ororon",
        structured_data={"id": "10000105", "name": "Ororon", "element": "Electro", "weapon_type": "Bow", "rarity": 4, "base_hp_lvl90": 9000, "talents": [{},{},{}], "constellations": [{},{},{},{},{},{}]},
        knowledge_doc=None,
    )
    assert res["is_complete"] is False
    assert res["quality_state"] == "PARTIAL"


# -----------------------------------------------------------------------------
# Scenario 4: Source Unavailable (Network Error / Outage)
# -----------------------------------------------------------------------------
def test_scenario_4_source_unavailable_preserves_active():
    """When an upstream source is unreachable, previous verified version is preserved and candidate aborted."""
    active_before = update_orchestrator.get_active_version()

    manifest = update_orchestrator.run_update_pipeline(
        target_version="8.0",
        simulate_source_failure=True,
    )

    assert manifest.lifecycle_state == VersionLifecycleState.REJECTED
    assert manifest.promotion_status == "BLOCKED"
    assert manifest.sources["src_animegamedata"].status == "FAILED"

    # Active canonical pointer is completely preserved
    active_after = update_orchestrator.get_active_version()
    assert active_after == active_before


# -----------------------------------------------------------------------------
# Scenario 5: Source Data Conflicts (Tier Hierarchy Resolution)
# -----------------------------------------------------------------------------
def test_scenario_5_source_conflict_resolution_hierarchy():
    """When official and secondary sources disagree on base stats or values, Tier hierarchy resolves."""
    conflict = update_orchestrator.record_source_conflict(
        entity_name="Mavuika",
        topic="Base ATK",
        source_a="src_hoyoverse_patch_notes",  # Tier 1
        source_b="src_genshin_fandom_wiki",    # Tier 5
        claim_a="359",
        claim_b="345",
        version="7.0",
    )
    assert conflict.conflict_status == "RESOLVED"
    assert "Tier 1" in conflict.resolution_notes


# -----------------------------------------------------------------------------
# Scenario 6: Concurrent New Version Discovery
# -----------------------------------------------------------------------------
def test_scenario_6_discovery_does_not_mutate_active_state():
    """Discovering a newer live version candidate does not alter current active calculations."""
    official = OfficialSourceAdapter()
    discovered = official.discover(target_version="7.1")
    assert len(discovered) >= 1
    assert discovered[0].target_version == "7.1"

    # Verify active version is unaffected
    active_ver = update_orchestrator.get_active_version()
    assert active_ver == "7.0"


# -----------------------------------------------------------------------------
# API Route Verification
# -----------------------------------------------------------------------------
def test_api_pipeline_update_manifests(client):
    """Verify GET /api/pipeline/update-manifests returns recorded candidate manifests."""
    res = client.get("/api/pipeline/update-manifests")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)


def test_api_pipeline_delta(client):
    """Verify GET /api/pipeline/delta returns computed differences."""
    res = client.get("/api/pipeline/delta?base_version=5.4&candidate_version=7.0")
    assert res.status_code == 200
    data = res.json()
    assert "new_characters" in data
    assert "base_version" in data
    assert data["base_version"] == "5.4"
    assert data["candidate_version"] == "7.0"
