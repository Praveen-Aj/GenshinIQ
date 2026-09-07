"""Unit and integration tests for GenshinIQ Version and Update Management System (Phase 2)."""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.version_service import version_service, parse_version_tuple
from backend.services.knowledge_service import knowledge_service
from backend.services.game_data_service import game_data_service

client = TestClient(app)


def test_parse_version_tuple():
    """Verify version tuple parsing."""
    assert parse_version_tuple("5.4") == (5, 4)
    assert parse_version_tuple("v5.4") == (5, 4)
    assert parse_version_tuple("1.0") == (1, 0)
    assert parse_version_tuple("invalid") == (0, 0)


def test_version_service_current():
    """Verify canonical current live game version is 5.4."""
    curr = version_service.get_current_version()
    assert curr.version == "5.4"
    assert "Dreams of Light" in curr.name
    assert curr.release_date == "2025-02-12"
    assert curr.is_current is True


def test_version_ordering_and_distance():
    """Verify distance calculation across official patch sequence."""
    dist_same = version_service.calculate_distance("5.4", "5.4")
    assert dist_same == 0

    dist_one = version_service.calculate_distance("5.3", "5.4")
    assert dist_one == 1

    dist_four = version_service.calculate_distance("5.0", "5.4")
    assert dist_four == 4

    dist_old = version_service.calculate_distance("1.0", "5.4")
    assert dist_old >= 35


def test_staleness_evaluation():
    """Verify staleness rules and warning generations."""
    # Current version
    eval_curr = version_service.evaluate_staleness("5.4")
    assert eval_curr.is_current is True
    assert eval_curr.is_stale is False
    assert eval_curr.version_distance == 0

    # Recent compatible version (e.g. 5.3)
    eval_recent = version_service.evaluate_staleness("5.3")
    assert eval_recent.is_current is False
    assert eval_recent.is_stale is False
    assert eval_recent.version_distance == 1

    # Stale version (4 patches behind)
    eval_stale = version_service.evaluate_staleness("5.0", stale_threshold_patches=4)
    assert eval_stale.is_stale is True
    assert eval_stale.version_distance == 4
    assert eval_stale.warning is not None
    assert "4 patches behind" in eval_stale.warning


def test_knowledge_version_filtering():
    """Verify filtering knowledge documents by version and staleness."""
    all_docs = knowledge_service.list_documents()
    assert len(all_docs) > 0

    # Filter with max_staleness_patches
    recent_docs = knowledge_service.list_documents(max_staleness_patches=2)
    assert len(recent_docs) > 0
    for doc in recent_docs:
        dist = version_service.calculate_distance(doc.metadata.game_version)
        assert dist <= 2

    # Verify stale documents detection
    stale_docs = knowledge_service.get_stale_documents(stale_threshold_patches=4)
    assert isinstance(stale_docs, list)
    for s in stale_docs:
        assert s["version_distance"] >= 4 or "5." not in s["document_version"]


def test_api_version_endpoints():
    """Verify API endpoints /api/version/current, /history, and /status."""
    # Current
    resp = client.get("/api/version/current")
    assert resp.status_code == 200
    cur_data = resp.json()
    assert cur_data["version"] == "5.4"
    assert cur_data["is_current"] is True

    # History
    resp_hist = client.get("/api/version/history")
    assert resp_hist.status_code == 200
    hist = resp_hist.json()
    assert len(hist) >= 38
    # Ensure newest first in history
    assert hist[0]["version"] == "5.4"

    # Status
    resp_stat = client.get("/api/version/status")
    assert resp_stat.status_code == 200
    stat = resp_stat.json()
    assert stat["current_version"] == "5.4"
    assert stat["total_tracked_versions"] >= 38
    assert stat["total_document_count"] > 0


def test_api_health_includes_game_version():
    """Verify /api/health includes validated game_version '5.4'."""
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["game_version"] == "5.4"
    assert "Dreams of Light" in data["game_patch_name"]


def test_character_data_version_fields():
    """Verify character data has canonical game_version_introduced populated."""
    kazuha = game_data_service.get_character("Kaedehara Kazuha")
    assert kazuha is not None
    assert kazuha.game_version_introduced == "1.6"
    assert kazuha.game_version_updated == "5.4"

    ayaka = game_data_service.get_character("Kamisato Ayaka")
    assert ayaka is not None
    assert ayaka.game_version_introduced == "2.0"

    furina = game_data_service.get_character("Furina")
    assert furina is not None
    assert furina.game_version_introduced == "4.2"
