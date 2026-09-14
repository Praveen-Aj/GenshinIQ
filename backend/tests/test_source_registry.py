"""Unit and integration tests for Phase 3: Provenance & Source Registry."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.chat import Citation
from backend.models.knowledge import KnowledgeDocument, KnowledgeMetadata, SourceType, compute_content_hash
from backend.models.source_registry import ConflictRecord, SourceTier, SourceType as RegSourceType
from backend.services.knowledge_service import knowledge_service
from backend.services.source_registry_service import source_registry_service

client = TestClient(app)


def test_source_registry_loading():
    """Verify central source registry loads with all required canonical sources and tiers."""
    sources = source_registry_service.list_sources()
    assert len(sources) >= 11

    # Check presence of all 5 tiers
    tiers_present = {s.tier for s in sources}
    assert SourceTier.TIER_1_OFFICIAL in tiers_present
    assert SourceTier.TIER_2_THEORYCRAFTING in tiers_present
    assert SourceTier.TIER_3_STRUCTURED_DATA in tiers_present
    assert SourceTier.TIER_4_STATISTICAL in tiers_present
    assert SourceTier.TIER_5_COMMUNITY in tiers_present

    # Check key sources
    official = source_registry_service.get_source("src_hoyoverse_official")
    assert official is not None
    assert official.tier == SourceTier.TIER_1_OFFICIAL
    assert official.source_type == RegSourceType.OFFICIAL
    assert official.trust_level == "AUTHORITATIVE"

    kqm = source_registry_service.get_source("src_kqm_guides")
    assert kqm is not None
    assert kqm.tier == SourceTier.TIER_2_THEORYCRAFTING
    assert kqm.source_type == RegSourceType.KQM
    assert kqm.trust_level == "CURATED_THEORYCRAFTING"

    amber = source_registry_service.get_source("src_project_amber")
    assert amber is not None
    assert amber.tier == SourceTier.TIER_3_STRUCTURED_DATA
    assert amber.source_type == RegSourceType.STRUCTURED_DATA

    wiki = source_registry_service.get_source("src_genshin_fandom_wiki")
    assert wiki is not None
    assert wiki.tier == SourceTier.TIER_5_COMMUNITY
    assert wiki.source_type == RegSourceType.COMMUNITY


def test_source_registry_filter_by_tier():
    """Verify querying sources by authority tier."""
    tier1 = source_registry_service.list_sources(tier=SourceTier.TIER_1_OFFICIAL)
    assert len(tier1) >= 2
    assert all(s.tier == SourceTier.TIER_1_OFFICIAL for s in tier1)

    tier2 = source_registry_service.list_sources(tier=SourceTier.TIER_2_THEORYCRAFTING)
    assert len(tier2) >= 2
    assert all(s.tier == SourceTier.TIER_2_THEORYCRAFTING for s in tier2)


def test_deterministic_content_hashing():
    """Verify deterministic SHA-256 computation across line-ending differences."""
    body_lf = "# Guide\n\nContent here with details."
    body_crlf = "# Guide\r\n\r\nContent here with details.  \r\n"

    hash_lf = compute_content_hash(body_lf)
    hash_crlf = compute_content_hash(body_crlf)

    assert hash_lf == hash_crlf
    assert len(hash_lf) == 64


def test_document_hash_verification():
    """Verify document hash verification passes for valid hash and fails for tampered content."""
    valid_content = "# Test Document\n\nThis is clean content."
    valid_hash = compute_content_hash(valid_content)

    meta = KnowledgeMetadata(
        source_id="src_kqm_guides",
        source="KeqingMains Guides (KQM)",
        source_url="https://keqingmains.com/test",
        canonical_url="https://keqingmains.com/test",
        source_type=SourceType.THEORYCRAFTING,
        authority_tier=2,
        topic="Character Guide",
        game_version="7.0",
        retrieved_at="2026-09-08T00:00:00Z",
        content_hash=valid_hash,
    )
    doc = KnowledgeDocument(
        id="test_doc",
        title="Test Document",
        metadata=meta,
        summary="Summary of test document",
        content=valid_content,
    )

    assert doc.verify_hash() is True

    # Tamper with content
    tampered_doc = KnowledgeDocument(
        id="test_doc",
        title="Test Document",
        metadata=meta,
        summary="Summary",
        content=valid_content + "\n[TAMPERED DATA]",
    )
    assert tampered_doc.verify_hash() is False


def test_invalid_source_id_rejected():
    """Verify that document with an unregistered source_id fails validation."""
    with pytest.raises(ValueError, match="Unregistered source_id"):
        KnowledgeMetadata(
            source_id="src_non_existent_fake_source",
            source="Unknown",
            source_url="https://fake.example.com",
            canonical_url="https://fake.example.com",
            source_type=SourceType.COMMUNITY,
            authority_tier=5,
            topic="Test",
            game_version="7.0",
            retrieved_at="2026-09-08T00:00:00Z",
            content_hash="a" * 64,
        )


def test_tier_mismatch_rejected():
    """Verify that claiming Tier 1 for a Tier 5 community source fails validation."""
    with pytest.raises(ValueError, match="Tier mismatch"):
        KnowledgeMetadata(
            source_id="src_genshin_fandom_wiki",
            source="Genshin Wiki",
            source_url="https://genshin-impact.fandom.com/wiki/Test",
            canonical_url="https://genshin-impact.fandom.com/wiki/Test",
            source_type=SourceType.COMMUNITY,
            authority_tier=1,  # ILLEGAL: Fandom wiki cannot claim Tier 1!
            topic="Test",
            game_version="7.0",
            retrieved_at="2026-09-08T00:00:00Z",
            content_hash="a" * 64,
        )


def test_zero_wiki_documents_labeled_authoritative():
    """Verify critical Phase 3 requirement: zero Fandom Wiki documents are labeled AUTHORITATIVE / Tier 1."""
    wiki_docs = [
        d for d in knowledge_service.documents.values()
        if d.metadata.source_id == "src_genshin_fandom_wiki" or "fandom.com" in d.metadata.source_url
    ]
    assert len(wiki_docs) == 146

    for doc in wiki_docs:
        assert doc.metadata.authority_tier == 5, f"{doc.id} must be Tier 5 Community"
        assert doc.metadata.source_type == SourceType.COMMUNITY, f"{doc.id} must be COMMUNITY source type"
        assert doc.metadata.source_type.value != "AUTHORITATIVE", f"{doc.id} must NOT be AUTHORITATIVE"
        assert doc.metadata.canonical_url is not None
        assert doc.metadata.retrieved_at is not None
        assert len(doc.metadata.content_hash) == 64


def test_all_production_documents_have_valid_hashes():
    """Verify every single loaded production knowledge document passes hash verification."""
    assert len(knowledge_service.documents) >= 178
    for doc_id, doc in knowledge_service.documents.items():
        assert doc.metadata.content_hash is not None, f"{doc_id} missing content_hash"
        assert len(doc.metadata.content_hash) == 64, f"{doc_id} has malformed content_hash"
        assert doc.verify_hash(), f"{doc_id} content hash does not match body!"
        assert doc.metadata.source_id in source_registry_service.sources, f"{doc_id} has unknown source_id"


def test_api_sources_list():
    """Verify GET /api/sources returns the registered canonical sources."""
    response = client.get("/api/sources")
    assert response.status_code == 200
    sources = response.json()
    assert len(sources) >= 11
    ids = [s["source_id"] for s in sources]
    assert "src_hoyoverse_official" in ids
    assert "src_kqm_guides" in ids
    assert "src_genshin_fandom_wiki" in ids


def test_api_sources_get_by_id():
    """Verify GET /api/sources/{source_id}."""
    response = client.get("/api/sources/src_kqm_tcl")
    assert response.status_code == 200
    data = response.json()
    assert data["source_id"] == "src_kqm_tcl"
    assert "KQM Theorycrafting Library" in data["name"]
    assert data["tier"] == 2

    # Not found check
    bad_res = client.get("/api/sources/non_existent_source")
    assert bad_res.status_code == 404


def test_api_knowledge_filtered_by_source_id_and_tier():
    """Verify filtering knowledge documents via API using source_id and authority_tier."""
    # Filter by source_id
    kqm_res = client.get("/api/knowledge/documents?source_id=src_kqm_guides")
    assert kqm_res.status_code == 200
    kqm_data = kqm_res.json()
    assert len(kqm_data) == 15
    assert all(d["metadata"]["source_id"] == "src_kqm_guides" for d in kqm_data)

    # Filter by authority_tier = 1
    t1_res = client.get("/api/knowledge/documents?authority_tier=1")
    assert t1_res.status_code == 200
    t1_data = t1_res.json()
    assert len(t1_data) == 3
    t1_ids = [d["id"] for d in t1_data]
    assert "official_combat_system_mechanics" in t1_ids
    assert "official_patch_5_0_nightsoul_notes" in t1_ids
    assert "official_patch_7_0_notes" in t1_ids


def test_citation_provenance_model():
    """Verify that Citation model cleanly exposes structured Phase 3 provenance."""
    citation = Citation(
        source_name="KeqingMains Guides (KQM)",
        source_url="https://keqingmains.com/arlecchino",
        snippet="Arlecchino guide snippet",
        character="Arlecchino",
        topic="Character Guide",
        game_version="7.0",
        document_id="kqm_arlecchino_extended_guide",
        source_id="src_kqm_guides",
        canonical_url="https://keqingmains.com/arlecchino",
        source_type="KQM",
        authority_tier=2,
        content_hash="abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
    )

    data = citation.model_dump()
    assert data["source_id"] == "src_kqm_guides"
    assert data["authority_tier"] == 2
    assert data["canonical_url"] == "https://keqingmains.com/arlecchino"
    assert data["content_hash"] is not None


def test_conflict_record_model():
    """Verify ConflictRecord captures auditable discrepancies between sources."""
    conflict = ConflictRecord(
        entity_name="Kazuha",
        topic="Elemental Mastery Scaling",
        source_a="src_hoyoverse_official",
        source_b="src_genshin_fandom_wiki",
        tier_a=SourceTier.TIER_1_OFFICIAL,
        tier_b=SourceTier.TIER_5_COMMUNITY,
        version_a="1.6",
        version_b="1.5",
        claim_a="Base elemental damage bonus scales with 0.04% per point of EM.",
        claim_b="Old text claimed 0.03% prior to patch 1.6 buff.",
        conflict_status="RESOLVED",
        detected_at="2026-09-08T00:00:00Z",
        resolution_notes="Official patch 1.6 and KQM verify 0.04%. Discard community wiki outdated claim.",
    )

    assert conflict.tier_a < conflict.tier_b
    assert conflict.conflict_status == "RESOLVED"
