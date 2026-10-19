"""
Unit and integration tests for Artifact Optimization Engine (Phase 15).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.artifact_optimizer_service import artifact_optimizer_service

client = TestClient(app)


def test_artifact_crit_value_calculation():
    """Verify exact formula CV = 2*CRIT_Rate + CRIT_DMG."""
    artifact = {
        "slot": "flower",
        "set_name": "Crimson Witch of Flames",
        "main_stat": "HP",
        "substats": [
            {"key": "critRate_", "name": "CRIT Rate", "value": 10.5},
            {"key": "critDMG_", "name": "CRIT DMG", "value": 21.0},
            {"key": "atk_", "name": "ATK%", "value": 5.8},
            {"key": "hp_", "name": "HP%", "value": 5.8}
        ]
    }
    res = artifact_optimizer_service.evaluate_artifact(artifact)
    # CV = 2 * 10.5 + 21.0 = 42.0
    assert res["crit_value"] == 42.0
    assert "Jewel" in res["cv_grade"]


def test_artifact_roll_value_calculation():
    """Verify Roll Value calculates percentage of maximum tier-4 rolls."""
    artifact = {
        "slot": "plume",
        "set_name": "Marechaussee Hunter",
        "main_stat": "ATK",
        "substats": [
            {"key": "critRate_", "name": "CRIT Rate", "value": 3.89},  # exactly 100% max roll
            {"key": "critDMG_", "name": "CRIT DMG", "value": 7.77},   # exactly 100% max roll
            {"key": "atk_", "name": "ATK%", "value": 5.83},           # exactly 100% max roll
            {"key": "enerRech_", "name": "Energy Recharge", "value": 6.48} # exactly 100% max roll
        ]
    }
    res = artifact_optimizer_service.evaluate_artifact(artifact)
    # Total RV = 100 + 100 + 100 + 100 = 400%
    assert round(res["total_roll_value_pct"], 0) == 400.0
    assert len(res["substats"]) == 4


def test_character_tailored_weights():
    """Stat weights should reflect character kit priorities (Hu Tao HP%/EM vs DEF)."""
    hu_tao_weights = artifact_optimizer_service.get_character_weights("Hu Tao")
    assert hu_tao_weights["hp_"] > hu_tao_weights["atk_"]
    assert hu_tao_weights["eleMas"] > hu_tao_weights["def_"]

    itto_weights = artifact_optimizer_service.get_character_weights("Arataki Itto")
    assert itto_weights["def_"] > itto_weights["hp_"]


def test_compare_two_artifacts():
    """Head-to-head comparison correctly recommends higher RV/CV artifact."""
    art_a = {
        "slot": "flower",
        "set_name": "Gladiator's Finale",
        "main_stat": "HP",
        "substats": [
            {"key": "critRate_", "name": "CRIT Rate", "value": 3.9},
            {"key": "critDMG_", "name": "CRIT DMG", "value": 7.8}
        ]
    }
    art_b = {
        "slot": "flower",
        "set_name": "Gladiator's Finale",
        "main_stat": "HP",
        "substats": [
            {"key": "critRate_", "name": "CRIT Rate", "value": 11.7},
            {"key": "critDMG_", "name": "CRIT DMG", "value": 23.4}
        ]
    }
    comp = artifact_optimizer_service.compare_two_artifacts(art_a, art_b, "Hu Tao")
    assert comp["recommended"] == "B"
    assert comp["cv_delta"] > 0
    assert comp["weighted_rv_delta"] > 0


def test_optimize_character_loadout_theoretical_fallback():
    """Should return theoretical benchmark build if bag is empty."""
    res = artifact_optimizer_service.optimize_character_loadout("Hu Tao")
    assert res["character"] == "Hu Tao"
    assert len(res["optimal_candidates"]) >= 1
    best = res["optimal_candidates"][0]
    assert len(best["artifacts"]) == 5
    assert best["total_crit_value"] > 100.0


def test_api_optimizer_endpoints():
    """Test all Phase 15 API routes."""
    # 1. Weights
    w_res = client.get("/api/optimizer/weights/Furina")
    assert w_res.status_code == 200
    assert "hp_" in w_res.json()["weights"]

    # 2. Evaluate single artifact
    art_payload = {
        "artifact": {
            "slot": "sands",
            "set_name": "Golden Troupe",
            "main_stat": "HP%",
            "substats": [
                {"key": "critRate_", "name": "CRIT Rate", "value": 7.0},
                {"key": "critDMG_", "name": "CRIT DMG", "value": 14.0}
            ]
        },
        "character_name": "Furina"
    }
    ev_res = client.post("/api/optimizer/evaluate-artifact", json=art_payload)
    assert ev_res.status_code == 200
    ev_data = ev_res.json()
    assert ev_data["crit_value"] == 28.0

    # 3. Optimize character loadout
    opt_payload = {
        "character_name": "Arlecchino",
        "min_er": 110.0,
        "max_results": 2
    }
    opt_res = client.post("/api/optimizer/character", json=opt_payload)
    assert opt_res.status_code == 200
    opt_data = opt_res.json()
    assert opt_data["character"] == "Arlecchino"
    assert len(opt_data["optimal_candidates"]) >= 1

    # 4. Compare artifacts
    cmp_payload = {
        "artifact_a": art_payload["artifact"],
        "artifact_b": {
            "slot": "sands",
            "set_name": "Golden Troupe",
            "main_stat": "HP%",
            "substats": [
                {"key": "critRate_", "name": "CRIT Rate", "value": 10.0},
                {"key": "critDMG_", "name": "CRIT DMG", "value": 20.0}
            ]
        },
        "character_name": "Furina"
    }
    cmp_res = client.post("/api/optimizer/compare", json=cmp_payload)
    assert cmp_res.status_code == 200
    assert cmp_res.json()["recommended"] == "B"
