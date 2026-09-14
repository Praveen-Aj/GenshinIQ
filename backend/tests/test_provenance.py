"""Tests for the provenance manifest endpoint."""

from fastapi.testclient import TestClient

from backend.main import app
from backend.services.game_data_service import game_data_service
from backend.services.knowledge_service import knowledge_service

client = TestClient(app)


def test_data_provenance_manifest_endpoint():
    response = client.get("/api/data/manifest")

    assert response.status_code == 200

    data = response.json()
    assert data["schema_version"] == "1.0"
    assert data["app_version"] == "0.3.0"
    assert data["game_data"]["characters"] == len(game_data_service.list_characters())
    assert data["game_data"]["weapons"] == len(game_data_service.list_weapons())
    assert data["game_data"]["artifact_sets"] == len(game_data_service.list_artifact_sets())
    assert data["game_data"]["materials"] == len(game_data_service.list_materials())
    assert data["knowledge_base"]["total_documents"] == len(knowledge_service.documents)
    assert data["knowledge_base"]["source_type_counts"]["COMMUNITY"] > 0
    assert data["knowledge_base"]["source_type_counts"]["OFFICIAL"] > 0
    assert data["knowledge_base"]["source_tier_counts"]["Tier 5"] >= 140
    assert data["knowledge_base"]["source_tier_counts"]["Tier 2"] >= 16
    assert data["knowledge_base"]["source_tier_counts"]["Tier 1"] >= 1
    assert len(data["game_data"]["aggregate_sha256"]) == 64
    assert len(data["knowledge_base"]["aggregate_sha256"]) == 64


def test_data_provenance_manifest_exposes_runtime_cache_dir():
    response = client.get("/api/data/manifest")

    assert response.status_code == 200
    assert response.json()["runtime_cache_dir"] == "data/runtime/showcases"
