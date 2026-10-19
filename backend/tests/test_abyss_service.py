"""
Unit and integration tests for Spiral Abyss & Endgame Tracker (Phase 17).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.abyss_service import abyss_service

client = TestClient(app)


def test_get_current_abyss_structure():
    """Verify active Floor 12 schedule, blessing, and 3 chambers."""
    abyss = abyss_service.get_current_abyss()
    assert abyss["floor"] == 12
    assert "blessing" in abyss
    assert "name" in abyss["blessing"]
    assert "effect" in abyss["blessing"]

    chambers = abyss["chambers"]
    assert len(chambers) == 3

    for ch in chambers:
        assert ch["chamber"] in (1, 2, 3)
        assert ch["level"] >= 95
        assert "first_half" in ch
        assert "second_half" in ch

        # Verify enemy metadata
        f_enemies = ch["first_half"]["enemies"]
        assert len(f_enemies) >= 1
        assert "hp" in f_enemies[0]
        assert "resistances" in f_enemies[0]
        assert "advisory" in f_enemies[0]


def test_abyss_grounded_recommendations():
    """Verify recommendations evaluate account ownership and provide side 1 / side 2 teams."""
    rec = abyss_service.get_grounded_recommendations()
    assert rec["floor"] == 12
    assert len(rec["side_1_recommendations"]) >= 1
    assert len(rec["side_2_recommendations"]) >= 1

    first_team = rec["side_1_recommendations"][0]
    assert "name" in first_team
    assert "members" in first_team
    assert len(first_team["members"]) == 4
    assert "fully_owned" in first_team
    assert "owned_count" in first_team


def test_api_abyss_endpoints():
    """Test API routes /api/abyss/current and /api/abyss/recommendations."""
    c_res = client.get("/api/abyss/current")
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert c_data["floor"] == 12
    assert len(c_data["chambers"]) == 3

    r_res = client.get("/api/abyss/recommendations")
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert "side_1_recommendations" in r_data
    assert "side_2_recommendations" in r_data
