import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.progression_service import progression_service

client = TestClient(app)

def test_ascension_cost_full_1_to_90():
    cost = progression_service.calculate_ascension_cost(
        "Arlecchino",
        current_level=1,
        target_level=90,
        current_ascension=0,
        target_ascension=6
    )
    assert "error" not in cost
    assert cost["character"] == "Arlecchino"
    assert cost["heros_wit"] == 419
    assert cost["total_mora"] == 420000 + 1672500  # 2,092,500 Mora
    mats = cost["materials_needed"]
    assert mats["Agnidus Agate Sliver"] == 1
    assert mats["Agnidus Agate Fragment"] == 9
    assert mats["Agnidus Agate Chunk"] == 9
    assert mats["Agnidus Agate Gemstone"] == 6

def test_talent_cost_1_to_10():
    cost = progression_service.calculate_talents_cost(
        "Arlecchino",
        current_normal=1,
        target_normal=1,
        current_skill=1,
        target_skill=10,
        current_burst=1,
        target_burst=10
    )
    assert "error" not in cost
    assert cost["crowns_needed"] == 2  # 1 for Skill + 1 for Burst
    mats = cost["materials_needed"]
    assert mats["Crown of Insight"] == 2
    # 2 talents 1->10: 2 * (3 Teachings, 21 Guides, 38 Philosophies)
    assert any("Teachings" in k and v == 6 for k, v in mats.items())
    assert any("Guide" in k and v == 42 for k, v in mats.items())
    assert any("Philosophies" in k and v == 76 for k, v in mats.items())
    assert mats["Mora"] == 1652500 * 2  # 3,305,000 Mora

def test_full_progression_with_resin_estimates():
    plan = progression_service.calculate_full_progression(
        "Furina",
        current_level=1,
        target_level=90,
        current_ascension=0,
        target_ascension=6,
        current_talents=[1, 1, 1],
        target_talents=[1, 10, 10]
    )
    assert "error" not in plan
    assert "resin_estimation" in plan
    resin = plan["resin_estimation"]
    assert resin["total_resin_needed"] > 1000
    assert resin["days_of_natural_resin"] > 5.0
    assert "World Bosses" in resin["resin_breakdown"]
    assert "Talent Domains" in resin["resin_breakdown"]

def test_inventory_shortfall_calculation():
    shortfall = progression_service.calculate_inventory_shortfall(
        "Arlecchino",
        target_level=90,
        target_ascension=6,
        target_talents=[1, 10, 10]
    )
    assert "error" not in shortfall
    assert shortfall["character"] == "Arlecchino"
    assert "shortfall_breakdown" in shortfall
    assert "missing_materials" in shortfall
    assert "shortfall_resin" in shortfall
    assert "today_farmable_materials" in shortfall
    assert isinstance(shortfall["today_farmable_materials"], list)

def test_progression_api_endpoints():
    # 1. Ascension endpoint
    res_asc = client.get("/api/progression/ascension?character=Arlecchino&current_level=1&target_level=90")
    assert res_asc.status_code == 200
    data_asc = res_asc.json()
    assert data_asc["heros_wit"] == 419

    # 2. Talents endpoint
    res_tal = client.get("/api/progression/talents?character=Arlecchino&target_skill=10&target_burst=10")
    assert res_tal.status_code == 200
    data_tal = res_tal.json()
    assert data_tal["crowns_needed"] == 2

    # 3. Full Character Progression plan
    res_full = client.get("/api/progression/character/Furina?target_level=90&skill_target=10&burst_target=10")
    assert res_full.status_code == 200
    data_full = res_full.json()
    assert "resin_estimation" in data_full

    # 4. Inventory Shortfall against account
    res_short = client.get("/api/progression/shortfall/Arlecchino?target_level=90")
    assert res_short.status_code == 200
    data_short = res_short.json()
    assert "shortfall_breakdown" in data_short

def test_progression_invalid_inputs_fail_closed():
    res = client.get("/api/progression/ascension?character=CompletelyFakeCharacter999")
    assert res.status_code == 404

    res_short = client.get("/api/progression/shortfall/NonexistentHero123")
    assert res_short.status_code == 404
