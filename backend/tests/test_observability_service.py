"""
Unit and integration tests for System Health & Observability Service (Phase 18).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.observability_service import observability_service

client = TestClient(app)


def test_detailed_diagnostics_structure():
    """Verify detailed diagnostics structure and metrics completeness."""
    diag = observability_service.get_detailed_diagnostics()
    assert diag["system_status"] == "HEALTHY"
    assert diag["uptime_seconds"] >= 0
    assert "started_at" in diag

    # Canonical Data
    c_data = diag["canonical_data"]
    assert c_data["total_entities"] >= 400
    assert c_data["character_count"] >= 80
    assert c_data["weapon_count"] >= 150
    assert len(c_data["dataset_checksums"]) >= 1

    # Knowledge Index
    k_data = diag["knowledge_index"]
    assert k_data["document_count"] >= 10
    assert k_data["vector_embedding_available"] is True
    assert k_data["bm25_lexical_available"] is True

    # Version System Alignment
    v_data = diag["version_system"]
    assert v_data["actual_current_version"] == "7.0"
    assert v_data["phase_8_allowed"] is False
    assert v_data["completeness_summary"] == "INCOMPLETE"


def test_telemetry_probe():
    """Verify lightweight liveness telemetry endpoint."""
    probe = observability_service.get_lightweight_telemetry()
    assert probe["status"] == "UP"
    assert probe["uptime_seconds"] >= 0
    assert probe["current_game_version"] == "7.0"


def test_zero_credential_leakage():
    """Verify zero API keys, secrets, or passwords in telemetry output."""
    diag = observability_service.get_detailed_diagnostics()
    diag_str = str(diag).lower()

    forbidden_terms = ["api_key", "gemini_api_key", "secret_key", "password", "private_key"]
    for term in forbidden_terms:
        assert term not in diag_str


def test_api_diagnostics_endpoints():
    """Test API routes /api/diagnostics/detailed and /api/diagnostics/telemetry."""
    det_res = client.get("/api/diagnostics/detailed")
    assert det_res.status_code == 200
    det_data = det_res.json()
    assert det_data["system_status"] == "HEALTHY"
    assert "canonical_data" in det_data

    tel_res = client.get("/api/diagnostics/telemetry")
    assert tel_res.status_code == 200
    tel_data = tel_res.json()
    assert tel_data["status"] == "UP"
