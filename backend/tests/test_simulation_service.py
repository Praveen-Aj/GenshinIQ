"""
Unit and integration tests for Combat Simulation Engine (Phase 16).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.simulation_service import simulation_service

client = TestClient(app)


def test_generate_gcsim_config():
    """Verify gcsim configuration syntax generation."""
    team = ["Arlecchino", "Yelan", "Bennett", "Zhongli"]
    res = simulation_service.generate_gcsim_config(team, duration_sec=90, iterations=500)
    assert res["valid"] is True
    assert "arlecchino char" in res["gcsim_config"]
    assert "target lvl=100" in res["gcsim_config"]
    assert "iteration=500" in res["gcsim_config"]
    assert "duration=90" in res["gcsim_config"]


def test_generate_gcsim_config_invalid_character():
    """Invalid character should safely return an error."""
    res = simulation_service.generate_gcsim_config(["InvalidCharName999"])
    assert "error" in res


def test_deterministic_simulation_metrics():
    """Simulation should compute positive DPS, character shares, and timeline."""
    team = ["Hu Tao", "Yelan", "Xingqiu", "Zhongli"]
    res = simulation_service.run_deterministic_simulation(team, duration_sec=20)
    assert res["valid"] is True
    assert res["summary_metrics"]["team_dps"] > 10000.0
    assert res["summary_metrics"]["total_damage"] > 200000.0

    # Character breakdown
    breakdown = res["character_breakdown"]
    assert len(breakdown) == 4
    total_share = sum(b["damage_share_pct"] for b in breakdown)
    assert 99.0 <= total_share <= 101.0

    # Main carry should deal substantial share
    hu_tao_entry = next(b for b in breakdown if b["character"] == "Hu Tao")
    assert hu_tao_entry["damage_share_pct"] >= 35.0

    # Timeline has duration data points
    assert len(res["dps_timeline"]) == 20


def test_deterministic_simulation_enemy_scaling():
    """Multi-target combat should increase total simulated damage."""
    team = ["Neuvillette", "Furina", "Kaedehara Kazuha", "Baizhu"]
    st_res = simulation_service.run_deterministic_simulation(team, duration_sec=15, enemy_count=1)
    aoe_res = simulation_service.run_deterministic_simulation(team, duration_sec=15, enemy_count=3)

    assert aoe_res["summary_metrics"]["team_dps"] > st_res["summary_metrics"]["team_dps"]


def test_api_simulation_endpoints():
    """Test API routes for running simulation and getting config."""
    # Run simulation
    payload = {
        "team": ["Arlecchino", "Bennett", "Kaedehara Kazuha", "Zhongli"],
        "duration_sec": 20,
        "enemy_count": 1,
        "enemy_res_pct": 10.0
    }
    r_res = client.post("/api/simulation/run", json=payload)
    assert r_res.status_code == 200
    r_data = r_res.json()
    assert r_data["valid"] is True
    assert r_data["summary_metrics"]["team_dps"] > 0

    # Run simulation invalid team
    inv_res = client.post("/api/simulation/run", json={"team": ["NonExistentChar"]})
    assert inv_res.status_code == 400

    # Config endpoint
    cfg_payload = {
        "team": ["Furina", "Neuvillette", "Kaedehara Kazuha", "Baizhu"],
        "duration_sec": 60,
        "iterations": 200
    }
    c_res = client.post("/api/simulation/config", json=cfg_payload)
    assert c_res.status_code == 200
    c_data = c_res.json()
    assert "neuvillette" in c_data["gcsim_config"]
