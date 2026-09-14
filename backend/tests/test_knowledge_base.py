"""Automated tests for Phase 3: Curated Knowledge Base."""

from fastapi.testclient import TestClient
from backend.main import app
from backend.services.knowledge_service import knowledge_service
from backend.models.knowledge import SourceType

client = TestClient(app)


def test_load_knowledge_documents():
    """Verify knowledge documents index loading and model validation."""
    assert len(knowledge_service.documents) >= 8

    # Check Arlecchino guide exists
    arle = knowledge_service.get_document("kqm_arlecchino_extended_guide")
    assert arle is not None
    assert arle.title == (
        "KQM Arlecchino Extended Character & Theorycrafting Guide"
    )
    assert "KeqingMains" in arle.metadata.source
    assert arle.metadata.source_type in (SourceType.KQM, SourceType.THEORYCRAFTING)
    assert arle.metadata.character == "Arlecchino"
    assert "Bond of Life" in arle.content


def test_list_knowledge_documents_with_filters():
    """Verify filters for character, topic, source_type, and version."""
    # Filter by character
    arle_docs = knowledge_service.list_documents(character="Arlecchino")
    assert len(arle_docs) >= 1
    assert any(d.id == "kqm_arlecchino_extended_guide" for d in arle_docs)

    # Filter by topic
    mechanics_docs = knowledge_service.list_documents(topic="Game Mechanics")
    assert len(mechanics_docs) >= 2
    ids = [d.id for d in mechanics_docs]
    assert "mechanics_bond_of_life" in ids
    assert "mechanics_elemental_reactions" in ids

    # Filter by source type
    tcl_docs = knowledge_service.list_documents(
        source_type=SourceType.TCL
    )
    assert len(tcl_docs) >= 8

    community_docs = knowledge_service.list_documents(
        source_type=SourceType.COMMUNITY
    )
    assert len(community_docs) >= 140


def test_get_document_by_id():
    """Verify retrieval of specific documents."""
    doc = knowledge_service.get_document("mechanics_bond_of_life")
    assert doc is not None
    assert doc.metadata.source_type == SourceType.TCL
    assert doc.metadata.authority_tier == 2
    assert doc.metadata.source_id == "src_kqm_tcl"
    assert doc.metadata.canonical_url == "https://library.keqingmains.com/"
    assert len(doc.metadata.content_hash) == 64
    assert "200% of their Max HP" in doc.content


def test_search_relevance():
    """Verify search relevance rankings."""
    # Search for "Bond of Life" should match both guides
    results = knowledge_service.search_documents("Bond of Life")
    assert len(results) >= 2
    ids = [r.id for r in results]
    assert "mechanics_bond_of_life" in ids
    assert "kqm_arlecchino_extended_guide" in ids

    # First result should be the dedicated mechanics page due to weight rules
    assert results[0].id == "mechanics_bond_of_life"


def test_api_list_documents():
    """Verify API endpoint GET /api/knowledge/documents."""
    response = client.get("/api/knowledge/documents?character=Furina")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert any(d["id"] == "kqm_furina_guide" for d in data)
    assert any(d["metadata"]["source_type"] in ("KQM", "THEORYCRAFTING") for d in data)


def test_api_get_document():
    """Verify API endpoint GET /api/knowledge/documents/{doc_id}."""
    response = client.get("/api/knowledge/documents/kqm_neuvillette_guide")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "kqm_neuvillette_guide"
    assert "Sourcewater Droplets" in data["content"]

    # Not found check
    response = client.get("/api/knowledge/documents/invalid_doc_id_here")
    assert response.status_code == 404


def test_api_search_knowledge():
    """Verify API endpoint GET /api/knowledge/search."""
    response = client.get("/api/knowledge/search?q=Nightsoul")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 1
    assert data[0]["id"] == "official_patch_5_0_nightsoul_notes"
    assert "Natlan" in data[0]["snippet"]
