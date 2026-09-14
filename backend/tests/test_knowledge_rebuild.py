"""Unit and integration tests for Phase 4: Knowledge Base Rebuild — Hard Factuality Verified."""

import json
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.knowledge import SourceType
from backend.models.source_registry import SourceTier
from backend.services.knowledge_service import knowledge_service
from backend.services.version_service import version_service

client = TestClient(app)
ROOT_DIR = Path(__file__).resolve().parent.parent.parent


def test_total_knowledge_documents_and_no_duplicates():
    """Verify knowledge base has expanded to 179 factual documents and has zero duplicate IDs."""
    docs = knowledge_service.documents
    assert len(docs) == 179

    # Ensure uniqueness of document IDs
    doc_ids = list(docs.keys())
    assert len(doc_ids) == len(set(doc_ids))


def test_v70_current_documents_coverage():
    """Verify exactly 17 v7.0 current documents exist and are marked as current."""
    current_docs = [
        d for d in knowledge_service.documents.values()
        if d.metadata.game_version == "7.0"
    ]
    assert len(current_docs) == 17
    assert all(d.metadata.freshness_status == "current" for d in current_docs)


def test_tier1_official_coverage():
    """Verify Tier 1 Official HoYoverse in-game combat specification (and absence of speculative launch docs)."""
    # Speculative unannounced patch doc must NOT exist in the knowledge base
    assert knowledge_service.get_document("official_patch_7_0_celestia_launch") is None
    assert knowledge_service.get_document("kqm_skirk_guide") is None

    # Verified in-game combat rules doc must exist
    combat_doc = knowledge_service.get_document("official_combat_system_mechanics")
    assert combat_doc is not None
    assert combat_doc.metadata.source_id == "src_genshin_ingame"
    assert combat_doc.metadata.authority_tier == SourceTier.TIER_1_OFFICIAL
    assert "Elemental Sight" in combat_doc.content
    assert "Stamina" in combat_doc.content
    assert combat_doc.verify_hash()


def test_tier2_kqm_meta_character_guides():
    """Verify newly ingested core meta character guides have valid KQM provenance and accurate mechanics."""
    characters_to_test = {
        "kqm_nahida_extended_guide": ("Nahida", "Tri-Karma Purification", "Deepwood"),
        "kqm_zhongli_extended_guide": ("Zhongli", "Jade Shield", "150%"),
        "kqm_bennett_extended_guide": ("Bennett", "Base ATK", "Fantastic Voyage"),
        "kqm_xiangling_extended_guide": ("Xiangling", "Pyronado", "0-ICD"),
        "kqm_xingqiu_extended_guide": ("Xingqiu", "Raincutter", "Sacrificial Sword"),
        "kqm_yelan_extended_guide": ("Yelan", "Depth-Clarion Dice", "Max HP"),
        "kqm_hu_tao_extended_guide": ("Hu Tao", "Guide to Afterlife", "Staff of Homa"),
        "kqm_alhaitham_extended_guide": ("Alhaitham", "Chisel-Light Mirrors", "Spread"),
    }

    for doc_id, (char_name, expected_kw1, expected_kw2) in characters_to_test.items():
        doc = knowledge_service.get_document(doc_id)
        assert doc is not None, f"Missing {doc_id}"
        assert doc.metadata.character == char_name
        assert doc.metadata.source_id == "src_kqm_guides"
        assert doc.metadata.authority_tier == SourceTier.TIER_2_THEORYCRAFTING
        assert doc.metadata.source_type == SourceType.KQM
        assert expected_kw1 in doc.content, f"{expected_kw1} missing in {doc_id}"
        assert expected_kw2 in doc.content, f"{expected_kw2} missing in {doc_id}"
        assert doc.verify_hash(), f"Hash verification failed on {doc_id}"


def test_tier2_tcl_advanced_mechanics():
    """Verify advanced theorycrafting mechanics documents from KQM TCL."""
    mechanics_to_test = {
        "mechanics_snapshotting_dynamic_buffs": ["Pyronado", "Stormbreaker", "Dynamic"],
        "mechanics_defense_resistance_math": ["DEF Multiplier", "Halving Rule", "Viridescent Venerer"],
        "mechanics_poise_interruption_resistance": ["Poise Health", "Interruption Resistance", "Hyperarmor"],
        "mechanics_aura_coexistence_dual_reactions": ["Electro-Charged", "Quicken", "Dual Reaction"],
    }

    for doc_id, keywords in mechanics_to_test.items():
        doc = knowledge_service.get_document(doc_id)
        assert doc is not None, f"Missing {doc_id}"
        assert doc.metadata.source_id == "src_kqm_tcl"
        assert doc.metadata.authority_tier == SourceTier.TIER_2_THEORYCRAFTING
        assert doc.metadata.source_type == SourceType.TCL
        for kw in keywords:
            assert kw in doc.content, f"{kw} missing in {doc_id}"
        assert doc.verify_hash(), f"Hash mismatch on {doc_id}"


def test_tier3_structured_data_bridges_no_speculation():
    """Verify Tier 3 structured data knowledge bridges contain no speculative or unreleased entries."""
    docs = [
        "structured_daily_talent_books_schedule",
        "structured_daily_weapon_materials_schedule",
        "structured_weekly_boss_conversions",
    ]
    for doc_id in docs:
        doc = knowledge_service.get_document(doc_id)
        assert doc is not None, f"Missing {doc_id}"
        assert doc.metadata.source_id == "src_project_amber"
        assert doc.metadata.authority_tier == SourceTier.TIER_3_STRUCTURED_DATA
        assert doc.metadata.source_type == SourceType.STRUCTURED_DATA
        assert doc.verify_hash(), f"Hash check failed on {doc_id}"

    # Specifically check that talent books schedule has 0 speculative entities
    talent_doc = knowledge_service.get_document("structured_daily_talent_books_schedule")
    assert "Snezhnaya" not in talent_doc.content
    assert "Celestia" not in talent_doc.content
    assert "Sandrone" not in talent_doc.content
    assert "Skirk" not in talent_doc.content
    assert "Varka" not in talent_doc.content


def test_knowledge_gaps_queue_file_grounded():
    """Verify that knowledge_gaps.json tracks genuine engine mechanics gaps, not fictional elements."""
    gaps_path = ROOT_DIR / "data" / "canonical" / "knowledge_gaps.json"
    assert gaps_path.exists()

    with open(gaps_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["schema_version"] == "1.0"
    assert data["total_gaps_tracked"] >= 3
    assert len(data["gaps"]) >= 3
    for gap in data["gaps"]:
        assert "gap_id" in gap
        assert "topic" in gap
        assert "version" in gap
        assert "status" in gap
        assert "recommended_source" in gap
        # Verify no fictional terms
        assert "lunaite" not in gap["gap_id"].lower()
        assert "sandrone" not in gap["gap_id"].lower()
        assert "varka" not in gap["gap_id"].lower()


def test_api_list_current_v70_documents():
    """Verify GET /api/knowledge/documents?game_version=7.0 returns the 17 current documents."""
    response = client.get("/api/knowledge/documents?game_version=7.0")
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 17
    assert all(d["metadata"]["game_version"] == "7.0" for d in docs)
    assert all(d["metadata"]["freshness_status"] == "current" for d in docs)
