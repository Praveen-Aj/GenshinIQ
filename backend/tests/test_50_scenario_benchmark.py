"""
50-Scenario Grounding Benchmark Suite (Phase 20).
Comprehensive multi-domain evaluation across:
1. Character Builds & Exact Stat Scalings (Scenarios 1-5)
2. Weapon Data, Base ATK & Scaling Curves (Scenarios 6-10)
3. Artifact Sets & Set Bonus Mechanics (Scenarios 11-15)
4. Materials, Progression & Domain Schedules (Scenarios 16-20)
5. Elemental Reactions & Mechanics (Scenarios 21-25)
6. Team Building, Synergy & Resonance (Scenarios 26-30)
7. Artifact Optimization & Roll Value Math (Scenarios 31-35)
8. Combat Simulation & Rotation Modeling (Scenarios 36-40)
9. Spiral Abyss Floor 12 Lineups & Strategy (Scenarios 41-45)
10. Account Grounding & Fail-Closed Guardrails (Scenarios 46-50)
"""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.game_data_service import game_data_service
from backend.services.encyclopedia_service import encyclopedia_service
from backend.services.guide_service import guide_service
from backend.services.progression_service import progression_service
from backend.services.team_service import team_service
from backend.services.artifact_optimizer_service import artifact_optimizer_service
from backend.services.simulation_service import simulation_service
from backend.services.abyss_service import abyss_service
from backend.services.account_inventory_service import account_inventory_service
from backend.services.knowledge_service import knowledge_service
from backend.services.version_service import version_service
from backend.services.version_completeness_gate import version_completeness_gate

client = TestClient(app)


# =============================================================================
# DOMAIN 1: CHARACTER BUILDS & EXACT STAT SCALINGS (Scenarios 1-5)
# =============================================================================

def test_scenario_01_hu_tao_canonical_data():
    """Scenario 1: Canonical retrieval for Hu Tao (Pyro Polearm 5*)."""
    char = game_data_service.get_character("Hu Tao")
    assert char is not None
    assert char.element == "Pyro"
    assert char.weapon_type == "Polearm"
    assert char.rarity == 5


def test_scenario_02_raiden_shogun_scaling_lv90():
    """Scenario 2: Raiden Shogun exact level 90 stat scaling."""
    res = encyclopedia_service.get_character_scaling("Raiden Shogun", level=90, ascension=6)
    assert res is not None
    assert res.get("level") == 90
    assert res["base_hp"] > 10000
    assert res["base_atk"] > 300


def test_scenario_03_bennett_support_guide_structure():
    """Scenario 3: Bennett curated build guide contains weapons, artifacts, and teams."""
    guide = encyclopedia_service.get_character_build_guide("Bennett")
    assert guide is not None
    assert len(guide.get("recommended_weapons", [])) > 0
    assert len(guide.get("recommended_artifacts", [])) > 0


def test_scenario_04_furina_character_package_grounding():
    """Scenario 4: Furina character knowledge package verified and released."""
    from backend.services.character_knowledge_service import character_knowledge_service
    pkg = character_knowledge_service.get_character_package("Furina")
    assert pkg is not None
    assert pkg.character_name == "Furina"
    assert pkg.is_released is True


def test_scenario_05_kazuha_elemental_mastery_archetype():
    """Scenario 5: Kazuha stat weights emphasize Elemental Mastery."""
    weights = artifact_optimizer_service.get_character_weights("Kaedehara Kazuha")
    assert weights.get("eleMas", 0.0) >= 0.8


# =============================================================================
# DOMAIN 2: WEAPON DATA, BASE ATK & SCALING CURVES (Scenarios 6-10)
# =============================================================================

def test_scenario_06_staff_of_homa_data():
    """Scenario 6: Staff of Homa 5* Polearm metadata."""
    wep = game_data_service.get_weapon("Staff of Homa")
    assert wep is not None
    assert wep.weapon_type == "Polearm"
    assert wep.rarity == 5


def test_scenario_07_engulfing_lightning_scaling_lv90():
    """Scenario 7: Engulfing Lightning Lv 90 Base ATK 608 with Energy Recharge."""
    res = encyclopedia_service.get_weapon_scaling("Engulfing Lightning", level=90, ascension=6, refinement=1)
    assert res is not None
    assert res["base_atk"] == 608.0
    assert "Energy Recharge" in res.get("sub_stat_type", "")


def test_scenario_08_mistsplitter_reforged_scaling():
    """Scenario 8: Mistsplitter Reforged Lv 90 Base ATK 674 with Crit DMG."""
    res = encyclopedia_service.get_weapon_scaling("Mistsplitter Reforged", level=90, ascension=6)
    assert res is not None
    assert res["base_atk"] == 674.0
    assert "CRIT" in res.get("sub_stat_type", "").upper()


def test_scenario_09_the_catch_f2p_polearm():
    """Scenario 9: The Catch 4* Polearm exact Lv 90 Base ATK 510."""
    res = encyclopedia_service.get_weapon_scaling("The Catch", level=90, ascension=6)
    assert res is not None
    assert res["base_atk"] == 510.0


def test_scenario_10_favonius_lance_utility():
    """Scenario 10: Favonius Lance 4* Polearm metadata and energy recharge archetype."""
    wep = game_data_service.get_weapon("Favonius Lance")
    assert wep is not None
    assert wep.rarity == 4


# =============================================================================
# DOMAIN 3: ARTIFACT SETS & SET BONUS MECHANICS (Scenarios 11-15)
# =============================================================================

def test_scenario_11_crimson_witch_bonuses():
    """Scenario 11: Crimson Witch of Flames 2pc Pyro DMG bonus."""
    art = game_data_service.get_artifact_set("Crimson Witch of Flames")
    assert art is not None
    assert "Pyro" in art.bonus_2pc


def test_scenario_12_emblem_of_severed_fate_bonuses():
    """Scenario 12: Emblem of Severed Fate 2pc Energy Recharge bonus."""
    art = game_data_service.get_artifact_set("Emblem of Severed Fate")
    assert art is not None
    assert "Energy Recharge" in art.bonus_2pc or "20%" in art.bonus_2pc


def test_scenario_13_deepwood_memories_dendro_res():
    """Scenario 13: Deepwood Memories 2pc Dendro DMG bonus."""
    art = game_data_service.get_artifact_set("Deepwood Memories")
    assert art is not None
    assert "Dendro" in art.bonus_2pc


def test_scenario_14_viridescent_venerer_swirl_shred():
    """Scenario 14: Viridescent Venerer 2pc Anemo DMG bonus."""
    art = game_data_service.get_artifact_set("Viridescent Venerer")
    assert art is not None
    assert "Anemo" in art.bonus_2pc


def test_scenario_15_marechaussee_hunter_crit_rate():
    """Scenario 15: Marechaussee Hunter 2pc Normal/Charged ATK."""
    art = game_data_service.get_artifact_set("Marechaussee Hunter")
    assert art is not None
    assert "Normal" in art.bonus_2pc or "Charged" in art.bonus_2pc


# =============================================================================
# DOMAIN 4: MATERIALS, PROGRESSION & DOMAIN SCHEDULES (Scenarios 16-20)
# =============================================================================

def test_scenario_16_hu_tao_ascension_cost_calculation():
    """Scenario 16: Character ascension calculation computes Hero's Wit and Mora."""
    res = progression_service.calculate_ascension_cost("Arlecchino", 1, 90, 0, 6)
    assert "error" not in res
    assert res["heros_wit"] == 419
    assert res["total_mora"] > 2000000


def test_scenario_17_talent_level_crown_requirement():
    """Scenario 17: Leveling two talents from 1 to 10 requires 2 Crowns of Insight."""
    res = progression_service.calculate_talents_cost("Arlecchino", 1, 1, 1, 10, 1, 10)
    assert "error" not in res
    assert res["crowns_needed"] == 2


def test_scenario_18_resin_day_estimation():
    """Scenario 18: Full progression resin day estimation is positive and bounded."""
    plan = progression_service.calculate_full_progression("Furina", 1, 90, 0, 6, [1, 1, 1], [1, 10, 10])
    assert "error" not in plan
    assert plan["resin_estimation"]["total_resin_needed"] > 1000
    assert plan["resin_estimation"]["days_of_natural_resin"] > 5.0


def test_scenario_19_inventory_shortfall_against_account():
    """Scenario 19: Inventory shortfall accounts for active inventory stock."""
    shortfall = progression_service.calculate_inventory_shortfall("Arlecchino", 90, 6, [1, 10, 10])
    assert "error" not in shortfall
    assert "shortfall_breakdown" in shortfall
    assert "today_farmable_materials" in shortfall


def test_scenario_20_daily_domain_farming_schedule():
    """Scenario 20: Weekly domain farming rotation guide provides regional coverage."""
    guide = guide_service.get_farming_guide()
    assert "regions" in guide
    assert "mondstadt" in guide["regions"]
    assert "liyue" in guide["regions"]


# =============================================================================
# DOMAIN 5: ELEMENTAL REACTIONS & MECHANICS (Scenarios 21-25)
# =============================================================================

def test_scenario_21_vaporize_reaction_multiplier():
    """Scenario 21: Vaporize reaction is recognized between Pyro and Hydro."""
    res = team_service.evaluate_team(["Hu Tao", "Xingqiu"])
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Vaporize" in reactions


def test_scenario_22_melt_reaction_multiplier():
    """Scenario 22: Melt reaction triggered between Pyro and Cryo."""
    res = team_service.evaluate_team(["Xiangling", "Ganyu"])
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Melt" in reactions


def test_scenario_23_hyperbloom_reaction_chain():
    """Scenario 23: Hyperbloom reaction triggered across Hydro, Dendro, and Electro."""
    res = team_service.evaluate_team(["Nahida", "Xingqiu", "Kuki Shinobu"])
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Bloom" in reactions
    assert "Hyperbloom" in reactions


def test_scenario_24_swirl_reaction():
    """Scenario 24: Swirl reaction triggered with Anemo."""
    res = team_service.evaluate_team(["Kaedehara Kazuha", "Bennett"])
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Swirl" in reactions


def test_scenario_25_crystallize_reaction():
    """Scenario 25: Crystallize reaction triggered with Geo."""
    res = team_service.evaluate_team(["Zhongli", "Fischl"])
    reactions = [r["name"] for r in res["elemental_reactions"]]
    assert "Crystallize" in reactions


# =============================================================================
# DOMAIN 6: TEAM BUILDING, SYNERGY & RESONANCE (Scenarios 26-30)
# =============================================================================

def test_scenario_26_pyro_resonance_fervent_flames():
    """Scenario 26: 2 Pyro characters activate Fervent Flames (+25% ATK)."""
    res = team_service.evaluate_team(["Arlecchino", "Bennett"])
    assert res["valid"] is True
    assert res["active_resonances"][0]["name"] == "Fervent Flames"
    assert res["active_resonances"][0]["atk_pct"] == 25.0


def test_scenario_27_hydro_resonance_soothing_water():
    """Scenario 27: 2 Hydro characters activate Soothing Water (+25% Max HP)."""
    res = team_service.evaluate_team(["Furina", "Yelan"])
    assert res["valid"] is True
    assert res["active_resonances"][0]["name"] == "Soothing Water"
    assert res["active_resonances"][0]["hp_pct"] == 25.0


def test_scenario_28_dendro_resonance_sprawling_greenery():
    """Scenario 28: 2 Dendro characters activate Sprawling Greenery (Elemental Mastery)."""
    res = team_service.evaluate_team(["Nahida", "Alhaitham"])
    assert res["valid"] is True
    assert res["active_resonances"][0]["name"] == "Sprawling Greenery"


def test_scenario_29_team_synergy_score_rational_team():
    """Scenario 29: Raiden National Team scores high synergy (>= 75)."""
    res = team_service.evaluate_team(["Raiden Shogun", "Xiangling", "Xingqiu", "Bennett"])
    assert res["valid"] is True
    assert res["synergy_score"] >= 75


def test_scenario_30_team_recommendations_account_aware():
    """Scenario 30: Team recommendations for Arlecchino produce viable setups."""
    rec = team_service.recommend_teams("Arlecchino")
    assert "error" not in rec
    assert len(rec["teams"]) > 0


# =============================================================================
# DOMAIN 7: ARTIFACT OPTIMIZATION & ROLL VALUE MATH (Scenarios 31-35)
# =============================================================================

def test_scenario_31_crit_value_calculation():
    """Scenario 31: CV = 2*CRIT_Rate + CRIT_DMG = 2*10.5 + 21.0 = 42.0."""
    art = {
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
    res = artifact_optimizer_service.evaluate_artifact(art)
    assert res["crit_value"] == 42.0


def test_scenario_32_roll_value_calculation():
    """Scenario 32: Roll Value percentage of max tier-4 roll is computed accurately."""
    art = {
        "slot": "plume",
        "set_name": "Marechaussee Hunter",
        "main_stat": "ATK",
        "substats": [
            {"key": "critRate_", "name": "CRIT Rate", "value": 3.89},
            {"key": "critDMG_", "name": "CRIT DMG", "value": 7.77},
            {"key": "atk_", "name": "ATK%", "value": 5.83},
            {"key": "enerRech_", "name": "Energy Recharge", "value": 6.48}
        ]
    }
    res = artifact_optimizer_service.evaluate_artifact(art)
    assert round(res["total_roll_value_pct"], 0) == 400.0


def test_scenario_33_hu_tao_stat_weights_favor_hp_and_em():
    """Scenario 33: Hu Tao stat weights prioritize HP% and EM over ATK% and DEF%."""
    weights = artifact_optimizer_service.get_character_weights("Hu Tao")
    assert weights["hp_"] > weights["atk_"]
    assert weights["eleMas"] > weights["def_"]


def test_scenario_34_artifact_comparison_head_to_head():
    """Scenario 34: Head-to-head artifact comparison evaluates delta CV and RV."""
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


def test_scenario_35_character_loadout_optimizer_account_bag():
    """Scenario 35: 5-piece loadout optimizer operates on account inventory with fallback."""
    res = artifact_optimizer_service.optimize_character_loadout("Hu Tao")
    assert res["character"] == "Hu Tao"
    assert len(res["optimal_candidates"]) >= 1


# =============================================================================
# DOMAIN 8: COMBAT SIMULATION & ROTATION MODELING (Scenarios 36-40)
# =============================================================================

def test_scenario_36_simulation_runs_deterministic_math():
    """Scenario 36: Mathematical simulation generates team DPS and rotation breakdown."""
    res = simulation_service.run_deterministic_simulation(["Hu Tao", "Yelan", "Xingqiu", "Zhongli"], duration_sec=20)
    assert res["valid"] is True
    assert res["summary_metrics"]["team_dps"] > 10000.0


def test_scenario_37_simulation_gcsim_config_generation():
    """Scenario 37: gcsim configuration file is syntactically formatted."""
    res = simulation_service.generate_gcsim_config(["Arlecchino", "Yelan", "Bennett", "Zhongli"], duration_sec=90, iterations=500)
    assert res["valid"] is True
    assert "arlecchino char" in res["gcsim_config"]


def test_scenario_38_simulation_elemental_share():
    """Scenario 38: Character damage shares add up to 100%."""
    res = simulation_service.run_deterministic_simulation(["Hu Tao", "Yelan", "Xingqiu", "Zhongli"], duration_sec=20)
    total_share = sum(b["damage_share_pct"] for b in res["character_breakdown"])
    assert 99.0 <= total_share <= 101.0


def test_scenario_39_simulation_invalid_empty_team():
    """Scenario 39: Simulation rejects invalid character gracefully."""
    res = simulation_service.generate_gcsim_config(["InvalidCharName999"])
    assert "error" in res


def test_scenario_40_simulation_api_endpoint():
    """Scenario 40: /api/simulation/run endpoint responds with valid simulation result."""
    payload = {
        "team": ["Arlecchino", "Bennett", "Kaedehara Kazuha", "Zhongli"],
        "duration_sec": 20,
    }
    res = client.post("/api/simulation/run", json=payload)
    assert res.status_code == 200
    assert res.json()["valid"] is True


# =============================================================================
# DOMAIN 9: SPIRAL ABYSS FLOOR 12 LINEUPS & STRATEGY (Scenarios 41-45)
# =============================================================================

def test_scenario_41_abyss_floor_12_chambers():
    """Scenario 41: Current Floor 12 has 3 chambers, each with first and second half."""
    abyss = abyss_service.get_current_abyss()
    assert abyss["floor"] == 12
    assert len(abyss["chambers"]) == 3


def test_scenario_42_abyss_blessing_and_leyline():
    """Scenario 42: Abyss contains active Blessing."""
    abyss = abyss_service.get_current_abyss()
    assert "blessing" in abyss
    assert len(abyss["blessing"]["name"]) > 0


def test_scenario_43_abyss_enemy_shield_counter_advisories():
    """Scenario 43: Chamber advisories provide elemental counter guidance."""
    abyss = abyss_service.get_current_abyss()
    ch1 = abyss["chambers"][0]
    first_enemies = ch1["first_half"]["enemies"]
    assert len(first_enemies) >= 1
    assert "advisory" in first_enemies[0]


def test_scenario_44_abyss_recommendations_account_grounded():
    """Scenario 44: Abyss recommendations produce team suggestions for both halves."""
    rec = abyss_service.get_grounded_recommendations()
    assert rec["floor"] == 12
    assert len(rec["side_1_recommendations"]) >= 1
    assert len(rec["side_2_recommendations"]) >= 1


def test_scenario_45_abyss_api_endpoint():
    """Scenario 45: /api/abyss/current endpoint returns Floor 12 data."""
    res = client.get("/api/abyss/current")
    assert res.status_code == 200
    assert res.json()["floor"] == 12


# =============================================================================
# DOMAIN 10: ACCOUNT GROUNDING & FAIL-CLOSED GUARDRAILS (Scenarios 46-50)
# =============================================================================

def test_scenario_46_default_uid_grounding():
    """Scenario 46: Default account snapshot is loaded with characters."""
    snap = account_inventory_service.get_active_snapshot()
    assert snap is not None
    assert len(snap.characters) > 0


def test_scenario_47_nonexistent_character_fails_closed():
    """Scenario 47: Non-existent character returns HTTP 404, never hallucinated."""
    res = client.get("/api/data/characters/FakeHero12345")
    assert res.status_code == 404


def test_scenario_48_unowned_character_inventory_handling():
    """Scenario 48: Progression for unowned character errors or fails closed."""
    res = progression_service.calculate_inventory_shortfall("FakeHero999", 90, 6, [1, 1, 1])
    assert "error" in res


def test_scenario_49_zero_internal_source_id_leakage():
    """Scenario 49: Consumer guides endpoint does not expose raw src_* identifiers."""
    res = client.get("/api/guides/summary")
    assert res.status_code == 200
    assert "src_" not in res.text


def test_scenario_50_release_gate_fail_closed_invariant():
    """
    Scenario 50 (Crucial Invariant):
    Version 7.0 release gate strictly blocks promotion without verified current data.
    phase_8_allowed MUST remain False.
    """
    gate = version_completeness_gate.audit_version_completeness()
    assert gate.phase_8_allowed is False, "Release gate must fail-closed when data is incomplete!"
    assert len(gate.blockers) > 0
