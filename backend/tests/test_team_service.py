"""
Unit and integration tests for Team Building Engine (Phase 14).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.team_service import team_service


client = TestClient(app)


def test_team_resonance_pyro():
    """Two Pyro characters should trigger Fervent Flames resonance."""
    res = team_service.evaluate_team(["Arlecchino", "Bennett"])
    assert res["valid"] is True
    assert len(res["active_resonances"]) == 1
    assert res["active_resonances"][0]["name"] == "Fervent Flames"
    assert res["active_resonances"][0]["atk_pct"] == 25.0


def test_team_resonance_dual():
    """Two Pyro and two Hydro characters should activate both Fervent Flames and Soothing Water."""
    res = team_service.evaluate_team(["Hu Tao", "Bennett", "Yelan", "Xingqiu"])
    assert res["valid"] is True
    res_names = [r["name"] for r in res["active_resonances"]]
    assert "Fervent Flames" in res_names
    assert "Soothing Water" in res_names
    assert len(res["active_resonances"]) == 2


def test_team_protective_canopy_resonance():
    """Four unique elements should trigger Protective Canopy."""
    res = team_service.evaluate_team(["Hu Tao", "Yelan", "Kaedehara Kazuha", "Zhongli"])
    assert res["valid"] is True
    res_names = [r["name"] for r in res["active_resonances"]]
    assert "Protective Canopy" in res_names


def test_team_role_balance_and_warnings():
    """A balanced team should have no glass cannon warning and high synergy score."""
    res = team_service.evaluate_team(["Arlecchino", "Yelan", "Bennett", "Zhongli"])
    assert res["valid"] is True
    assert res["synergy_score"] >= 80
    assert len(res["warnings"]) == 0
    assert len(res["rotation_flow"]) >= 4

    # Now test glass cannon (no sustain)
    glass_res = team_service.evaluate_team(["Arlecchino", "Yelan", "Xingqiu", "Kaedehara Kazuha"])
    assert glass_res["valid"] is True
    assert any("Glass Cannon" in w for w in glass_res["warnings"])

    # Now test conflict (too many main DPS)
    conflict_res = team_service.evaluate_team(["Arlecchino", "Hu Tao", "Xiao", "Zhongli"])
    assert conflict_res["valid"] is True
    assert any("On-field Conflict" in w for w in conflict_res["warnings"])


def test_team_reactions_unlocked():
    """Pyro + Hydro + Anemo should unlock Vaporize and Swirl reactions."""
    res = team_service.evaluate_team(["Hu Tao", "Yelan", "Kaedehara Kazuha"])
    assert res["valid"] is True
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Vaporize" in reactions
    assert "Swirl" in reactions


def test_team_invalid_and_boundary_conditions():
    """Should cleanly handle empty lists, unknown characters, and teams > 4."""
    empty_res = team_service.evaluate_team([])
    assert "error" in empty_res

    unknown_res = team_service.evaluate_team(["FakeCharName123"])
    assert "error" in unknown_res
    assert unknown_res["valid"] is False

    too_large_res = team_service.evaluate_team(["Arlecchino", "Bennett", "Yelan", "Xingqiu", "Zhongli"])
    assert "error" in too_large_res
    assert too_large_res["valid"] is False


def test_recommend_teams():
    """Should return curated team setups with ownership status."""
    rec = team_service.recommend_teams("Arlecchino")
    assert rec["focal_character"] == "Arlecchino"
    assert len(rec["teams"]) > 0
    first_team = rec["teams"][0]
    assert "members" in first_team
    assert "fully_owned_on_account" in first_team
    assert "missing_from_account" in first_team

    # Non-existent character
    missing = team_service.recommend_teams("NonExistentHero")
    assert "error" in missing


def test_api_team_endpoints():
    """Test API routes for team evaluation, recommendations, and resonances."""
    # Resonances
    r_res = client.get("/api/teams/resonances")
    assert r_res.status_code == 200
    assert "Pyro" in r_res.json()
    assert "Hydro" in r_res.json()

    # Evaluate POST
    payload = {"characters": ["Arlecchino", "Yelan", "Bennett", "Zhongli"]}
    e_res = client.post("/api/teams/evaluate", json=payload)
    assert e_res.status_code == 200
    data = e_res.json()
    assert data["valid"] is True
    assert data["synergy_score"] >= 80

    # Evaluate POST invalid character
    inv_res = client.post("/api/teams/evaluate", json={"characters": ["InvalidHeroName"]})
    assert inv_res.status_code == 400

    # Recommend GET
    rec_res = client.get("/api/teams/recommend/Furina")
    assert rec_res.status_code == 200
    rec_data = rec_res.json()
    assert rec_data["focal_character"] == "Furina"

