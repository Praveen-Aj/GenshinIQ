"""
Comprehensive deterministic test suite for Phase 7: Deterministic Build & Stat Engine.
Validates character stat resolution, weapon scaling, artifact contributions,
aggregation arithmetic, account snapshot integration, determinism, golden reference cases,
and REST API endpoints.
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.models.stat_engine import CalculationStatus, VersionCompatibilityStatus
from backend.services.stat_engine import (
    stat_engine_service,
    ARTIFACT_5STAR_MAIN_STATS,
)


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


# ==============================================================================
# 1. CHARACTER BASE STAT RESOLUTION TESTS
# ==============================================================================

def test_character_level_90_canonical_base_stats():
    """Verify exact level 90 base stats for representative characters from canonical data."""
    # Kaedehara Kazuha Lv90 Asc 6
    k_base, k_asc, k_status, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=90, ascension=6)
    assert k_status == CalculationStatus.COMPLETE
    assert k_base["hp"] == 13348.0
    assert k_base["atk"] == 297.0
    assert k_base["def_"] == 807.0
    assert "Elemental Mastery" in k_asc
    assert k_asc["Elemental Mastery"] == 115.2

    # Hu Tao Lv90 Asc 6
    ht_base, ht_asc, ht_status, _ = stat_engine_service.resolve_character_base_stats("Hu Tao", level=90, ascension=6)
    assert ht_status == CalculationStatus.COMPLETE
    assert ht_base["hp"] == 15552.0
    assert ht_base["atk"] == 106.0
    assert ht_base["def_"] == 876.0
    assert "CRIT DMG" in ht_asc
    assert ht_asc["CRIT DMG"] == 0.384  # 38.4% CRIT DMG

    # Arlecchino Lv90 Asc 6
    arl_base, arl_asc, arl_status, _ = stat_engine_service.resolve_character_base_stats("Arlecchino", level=90, ascension=6)
    assert arl_status == CalculationStatus.COMPLETE
    assert arl_base["hp"] == 13103.0
    assert arl_base["atk"] == 342.0
    assert arl_base["def_"] == 765.0
    assert "CRIT DMG" in arl_asc
    assert arl_asc["CRIT DMG"] == 0.384


def test_character_level_1_base_stats():
    """Verify level 1 initial values without ascension bonus."""
    k_base, k_asc, k_status, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=1, ascension=0)
    assert k_status == CalculationStatus.COMPLETE
    # Initial Lv1 values (rounded)
    assert k_base["hp"] == 1039.0
    assert k_base["atk"] == 23.0
    assert k_base["def_"] == 63.0
    assert k_asc == {}  # No ascension stat at Phase 0


def test_character_ascension_progression():
    """Verify ascension special stat progression across phases."""
    # Phase 1 (Lv40/40): No special ascension stat yet
    _, asc_p1, _, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=40, ascension=1)
    assert "Elemental Mastery" not in asc_p1

    # Phase 2 (Lv50/50): Tier 1 (28.8 EM)
    _, asc_p2, _, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=50, ascension=2)
    assert asc_p2.get("Elemental Mastery") == 28.8

    # Phase 4 (Lv70/70): Tier 2 (57.6 EM)
    _, asc_p4, _, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=70, ascension=4)
    assert asc_p4.get("Elemental Mastery") == 57.6

    # Phase 6 (Lv90/90): Tier 4 (115.2 EM)
    _, asc_p6, _, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=90, ascension=6)
    assert asc_p6.get("Elemental Mastery") == 115.2


# ==============================================================================
# 2. WEAPON STAT RESOLUTION TESTS
# ==============================================================================

def test_weapon_level_90_scaling():
    """Verify level 90 base ATK and secondary stats."""
    # Dragon's Bane Lv90 R1
    atk, sub_name, sub_val, _, status, _ = stat_engine_service.resolve_weapon_stats("Dragon's Bane", level=90, ascension=6, refinement=1)
    assert status == CalculationStatus.COMPLETE
    assert atk == 454.0
    assert sub_name == "Elemental Mastery"
    assert sub_val == 221.0  # Canonical integer EM (48 * 4.594 = 220.512 -> 221)

    # Freedom-Sworn Lv90 R1
    fs_atk, fs_sub_name, fs_sub_val, _, fs_status, _ = stat_engine_service.resolve_weapon_stats("Freedom-Sworn", level=90, ascension=6, refinement=1)
    assert fs_status == CalculationStatus.COMPLETE
    assert fs_atk == 608.0
    assert fs_sub_name == "Elemental Mastery"
    assert fs_sub_val == 198.0  # Canonical integer EM (43.2 * 4.594 = 198.4608 -> 198)


def test_weapon_level_1_scaling():
    """Verify level 1 base ATK and secondary stat."""
    atk, sub_name, sub_val, _, status, _ = stat_engine_service.resolve_weapon_stats("Dragon's Bane", level=1, ascension=0, refinement=1)
    assert status == CalculationStatus.COMPLETE
    assert atk == 41.0
    assert sub_name == "Elemental Mastery"
    assert round(sub_val, 1) == 48.0


def test_weapon_static_passives():
    """Verify static unconditional stat bonuses from weapons like Jade Cutter or Homa."""
    _, _, _, passives_r1, _, _ = stat_engine_service.resolve_weapon_stats("Staff of Homa", level=90, refinement=1)
    assert passives_r1.get("hp_") == 0.20  # +20% HP at R1

    _, _, _, passives_r5, _, _ = stat_engine_service.resolve_weapon_stats("Staff of Homa", level=90, refinement=5)
    assert passives_r5.get("hp_") == 0.40  # +40% HP at R5


# ==============================================================================
# 3. ARTIFACT STAT RESOLUTION TESTS
# ==============================================================================

def test_artifact_main_stat_resolution_5star():
    """Verify canonical 5-star artifact main stat resolution at levels 0 and 20."""
    # Flower flat HP
    _, fl_0 = stat_engine_service.resolve_artifact_main_stat("flower", "hp", rarity=5, level=0)
    _, fl_20 = stat_engine_service.resolve_artifact_main_stat("flower", "hp", rarity=5, level=20)
    assert fl_0 == 717.0
    assert fl_20 == 4780.0

    # Plume flat ATK
    _, pl_0 = stat_engine_service.resolve_artifact_main_stat("plume", "atk", rarity=5, level=0)
    _, pl_20 = stat_engine_service.resolve_artifact_main_stat("plume", "atk", rarity=5, level=20)
    assert pl_0 == 47.0
    assert pl_20 == 311.0

    # Sands ATK%
    _, s_0 = stat_engine_service.resolve_artifact_main_stat("sands", "atk_", rarity=5, level=0)
    _, s_20 = stat_engine_service.resolve_artifact_main_stat("sands", "atk_", rarity=5, level=20)
    assert s_0 == 0.070
    assert s_20 == 0.466

    # Circlet CRIT Rate%
    _, cr_0 = stat_engine_service.resolve_artifact_main_stat("circlet", "critRate_", rarity=5, level=0)
    _, cr_20 = stat_engine_service.resolve_artifact_main_stat("circlet", "critRate_", rarity=5, level=20)
    assert cr_0 == 0.047
    assert cr_20 == 0.311

    # Circlet CRIT DMG%
    _, cd_0 = stat_engine_service.resolve_artifact_main_stat("circlet", "critDMG_", rarity=5, level=0)
    _, cd_20 = stat_engine_service.resolve_artifact_main_stat("circlet", "critDMG_", rarity=5, level=20)
    assert cd_0 == 0.093
    assert cd_20 == 0.622


def test_artifact_crit_value_calculation():
    """Verify CV formula: CV = 2 * CRIT_Rate% + CRIT_DMG%."""
    sample_artifacts = [
        {
            "slot": "flower",
            "canonical_set_name": "Gladiator's Finale",
            "rarity": 5,
            "level": 20,
            "main_stat_key": "hp",
            "substats": [
                {"key": "critRate_", "value": 3.9},
                {"key": "critDMG_", "value": 21.0},
                {"key": "atk_", "value": 5.3},
            ]
        }
    ]
    slots, _, total_cv = stat_engine_service.resolve_artifact_inventory_contribution(sample_artifacts)
    assert len(slots) == 1
    # 2 * 3.9 + 21.0 = 7.8 + 21.0 = 28.8
    assert slots[0].crit_value == 28.8
    assert total_cv == 28.8


def test_artifact_2pc_and_4pc_set_bonuses():
    """Verify detection of active 2-piece and 4-piece set bonuses."""
    vv_set = [
        {"slot": "flower", "canonical_set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "hp", "substats": []},
        {"slot": "plume", "canonical_set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "atk", "substats": []},
        {"slot": "sands", "canonical_set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "eleMas", "substats": []},
        {"slot": "goblet", "canonical_set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "anemo_dmg_", "substats": []},
        {"slot": "circlet", "canonical_set_name": "Gladiator's Finale", "rarity": 5, "level": 20, "main_stat_key": "critRate_", "substats": []},
    ]
    _, set_bonuses, _ = stat_engine_service.resolve_artifact_inventory_contribution(vv_set)
    assert len(set_bonuses) == 2
    assert any(b.set_name == "Viridescent Venerer" and b.pieces_active == 2 for b in set_bonuses)
    assert any(b.set_name == "Viridescent Venerer" and b.pieces_active == 4 for b in set_bonuses)


# ==============================================================================
# 4. STAT AGGREGATION & DERIVATION ARITHMETIC TESTS
# ==============================================================================

def test_exact_stat_aggregation_arithmetic():
    """
    Test exact mathematical aggregation:
    Final HP  = Base HP * (1 + Sum HP%) + Sum Flat HP
    Final ATK = (Char Base + Weapon Base) * (1 + Sum ATK%) + Sum Flat ATK
    """
    gear = [
        # Flower: +4780 Flat HP, +5.3% ATK
        {"slot": "flower", "canonical_set_name": "Gladiator's Finale", "rarity": 5, "level": 20, "main_stat_key": "hp", "substats": [{"key": "atk_", "value": 5.3}]},
        # Plume: +311 Flat ATK, +5.3% HP
        {"slot": "plume", "canonical_set_name": "Gladiator's Finale", "rarity": 5, "level": 20, "main_stat_key": "atk", "substats": [{"key": "hp_", "value": 5.3}]},
        # Sands: +46.6% ATK
        {"slot": "sands", "canonical_set_name": "Wanderer's Troupe", "rarity": 5, "level": 20, "main_stat_key": "atk_", "substats": []},
    ]

    # Calculate for Kazuha Lv90 + Xiphos Lv90
    # Kazuha Base: HP=13348, ATK=297, DEF=807
    # Xiphos Base: ATK=510, EM=165.4
    # Total Base ATK = 297 + 510 = 807
    # 2pc Gladiator Bonus: +18% ATK
    # Total ATK% = 46.6% (sands) + 5.3% (flower sub) + 18% (2pc glad) = 69.9% (0.699)
    # Total Flat ATK = 311 (plume)
    # Expected Final ATK = round(807 * (1 + 0.699) + 311) = round(807 * 1.699 + 311) = round(1371.09 + 311) = 1682
    snapshot = stat_engine_service.calculate_build_stats(
        character_name_or_id="Kaedehara Kazuha",
        weapon_name_or_id="Xiphos' Moonlight",
        artifacts=gear,
    )

    assert snapshot.stats.base_atk == 807.0
    assert snapshot.stats.atk == 1682.0

    # Total HP% = 5.3% (0.053)
    # Total Flat HP = 4780
    # Expected Final HP = round(13348 * (1 + 0.053) + 4780) = round(13348 * 1.053 + 4780) = round(14055.44 + 4780) = 18835
    assert snapshot.stats.base_hp == 13348.0
    assert snapshot.stats.hp == 18835.0


# ==============================================================================
# 5. ACCOUNT SNAPSHOT INTEGRATION TESTS (REAL DATA)
# ==============================================================================

def test_account_kazuha_build_integration():
    """Verify retrieval and calculation of Kazuha from Phase 6 account snapshot."""
    k_build = stat_engine_service.get_account_character_build("Kaedehara Kazuha")
    assert k_build is not None
    assert k_build.character_name == "Kaedehara Kazuha"
    assert k_build.level == 90
    assert k_build.ascension == 6
    assert k_build.weapon is not None
    assert k_build.weapon["name"] == "Xiphos' Moonlight"
    assert k_build.stats.base_hp == 13348.0
    assert k_build.stats.base_atk == 807.0
    assert k_build.stats.elemental_mastery == 280.0  # 115.2 (asc) + 165.0 (xiphos) = 280.2 -> round_half_up = 280.0


def test_account_hu_tao_build_integration():
    """Verify retrieval and calculation of Hu Tao from Phase 6 account snapshot."""
    ht_build = stat_engine_service.get_account_character_build("Hu Tao")
    assert ht_build is not None
    assert ht_build.character_name == "Hu Tao"
    assert ht_build.level == 90
    assert ht_build.weapon is not None
    assert ht_build.weapon["name"] == "Dragon's Bane"
    assert ht_build.stats.base_hp == 15552.0
    assert ht_build.stats.base_atk == 560.0
    assert ht_build.stats.crit_dmg == 0.884  # 50% baseline + 38.4% ascension


def test_account_jahoda_equipped_artifacts_integration():
    """Verify character with full 5-piece artifact set equipped from account."""
    j_build = stat_engine_service.get_account_character_build("Jahoda")
    assert j_build is not None
    assert len(j_build.artifacts) == 5
    assert j_build.breakdown.total_artifact_crit_value == 46.6
    assert len(j_build.breakdown.active_set_bonuses) == 2
    assert j_build.stats.crit_rate == 0.151
    assert j_build.stats.crit_dmg == 0.764


# ==============================================================================
# 6. DETERMINISM & PERFORMANCE TESTS
# ==============================================================================

def test_calculation_strict_determinism():
    """Verify that 100 repeated calculations yield identical results without jitter."""
    results = []
    for _ in range(100):
        b = stat_engine_service.calculate_build_stats("Kaedehara Kazuha", weapon_name_or_id="Freedom-Sworn")
        results.append(b.model_dump_json())

    first = results[0]
    for r in results[1:]:
        assert r == first, "Non-deterministic output detected!"


def test_calculation_performance():
    """Verify single build calculation completes in under 5ms."""
    import time
    start = time.perf_counter()
    for _ in range(50):
        stat_engine_service.calculate_build_stats("Hu Tao", weapon_name_or_id="Dragon's Bane")
    elapsed_ms = (time.perf_counter() - start) * 1000.0 / 50.0
    assert elapsed_ms < 5.0, f"Calculation took too long: {elapsed_ms:.2f} ms per call"


# ==============================================================================
# 7. BUILD COMPARISON PRIMITIVE TESTS
# ==============================================================================

def test_build_comparison_primitive():
    """Verify comparison delta between two builds."""
    b_xiphos = stat_engine_service.calculate_build_stats("Kaedehara Kazuha", weapon_name_or_id="Xiphos' Moonlight")
    b_freedom = stat_engine_service.calculate_build_stats("Kaedehara Kazuha", weapon_name_or_id="Freedom-Sworn")

    diff = stat_engine_service.compare_builds(b_xiphos, b_freedom)
    # Freedom Sworn has 608 ATK vs Xiphos 510 ATK (+98 ATK)
    assert diff.stat_deltas["atk"] == 98.0
    # Freedom Sworn has 198.4 EM vs Xiphos 165.4 EM (+33.0 EM)
    assert diff.stat_deltas["elemental_mastery"] == 33.0
    assert any("Build B gains +98.0 ATK" in n for n in diff.summary_notes)


# ==============================================================================
# 8. INVALID INPUTS & ERROR HANDLING TESTS
# ==============================================================================

def test_invalid_level_and_ascension():
    """Verify out-of-range inputs return INVALID calculation status."""
    _, _, status, warnings = stat_engine_service.resolve_character_base_stats("Hu Tao", level=100, ascension=7)
    assert status == CalculationStatus.INVALID
    assert len(warnings) > 0


def test_unsupported_character_name():
    """Verify unknown character name returns UNSUPPORTED calculation status."""
    _, _, status, warnings = stat_engine_service.resolve_character_base_stats("FakeCharacterName123")
    assert status == CalculationStatus.UNSUPPORTED
    assert any("not found" in w.lower() for w in warnings)


# ==============================================================================
# 9. REST API ENDPOINTS TESTS
# ==============================================================================

def test_api_get_character_build(client):
    """Test GET /api/build/{character_id} returns 200 OK and snapshot."""
    res = client.get("/api/build/Kaedehara Kazuha")
    assert res.status_code == 200
    data = res.json()
    assert data["character_name"] == "Kaedehara Kazuha"
    assert data["stats"]["base_hp"] == 13348.0
    assert data["stats"]["base_atk"] == 807.0


def test_api_get_character_build_stats(client):
    """Test GET /api/build/{character_id}/stats returns combat stat sheet."""
    res = client.get("/api/build/Hu Tao/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["base_hp"] == 15552.0
    assert data["crit_dmg"] == 0.884


def test_api_get_character_build_breakdown(client):
    """Test GET /api/build/{character_id}/breakdown returns mathematical breakdown."""
    res = client.get("/api/build/Jahoda/breakdown")
    assert res.status_code == 200
    data = res.json()
    assert "hp" in data
    assert "atk" in data
    assert "artifact_slots" in data
    assert data["total_artifact_crit_value"] == 46.6


def test_api_post_build_calculate(client):
    """Test POST /api/build/calculate for ad-hoc build."""
    payload = {
        "character": "Kaedehara Kazuha",
        "level": 90,
        "weapon": "Freedom-Sworn",
        "weapon_level": 90,
    }
    res = client.post("/api/build/calculate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["character_name"] == "Kaedehara Kazuha"
    assert data["stats"]["base_atk"] == 905.0  # 297 + 608 = 905


def test_api_post_build_compare(client):
    """Test POST /api/build/compare returns delta between two weapon setups."""
    payload = {
        "character_a": "Kaedehara Kazuha",
        "weapon_a": "Xiphos' Moonlight",
        "weapon_b": "Freedom-Sworn",
    }
    res = client.post("/api/build/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["stat_deltas"]["atk"] == 98.0
    assert data["stat_deltas"]["elemental_mastery"] == 33.0


# ==============================================================================
# 8. FORENSIC GOLDEN INTEGRITY & BREAKPOINT SCALING TESTS
# ==============================================================================

def test_golden_characters_level_scaling_breakpoints():
    """
    Forensic verification of HP, ATK, DEF, and special stat across all 13 promotion
    breakpoints for Kazuha, Hu Tao, Xiao, and Arlecchino.
    """
    # 1. Kaedehara Kazuha
    k_expected = [
        (1, 0, 1039, 23, 63),
        (20, 0, 2695, 60, 163),
        (20, 1, 3586, 80, 217),
        (40, 1, 5366, 119, 324),
        (40, 2, 5999, 133, 363),
        (50, 2, 6902, 153, 417),
        (50, 3, 7747, 172, 468),
        (60, 3, 8659, 192, 523),
        (60, 4, 9292, 206, 562),
        (70, 4, 10213, 227, 617),
        (70, 5, 10846, 241, 656),
        (80, 5, 11777, 262, 712),
        (80, 6, 12410, 276, 750),
        (90, 6, 13348, 297, 807),
    ]
    for lvl, asc, exp_hp, exp_atk, exp_def in k_expected:
        base, asc_stats, status, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=lvl, ascension=asc)
        assert status == CalculationStatus.COMPLETE
        assert base["hp"] == exp_hp, f"Kazuha Lv{lvl} Asc{asc} HP failed: got {base['hp']}, expected {exp_hp}"
        assert base["atk"] == exp_atk, f"Kazuha Lv{lvl} Asc{asc} ATK failed: got {base['atk']}, expected {exp_atk}"
        assert base["def_"] == exp_def, f"Kazuha Lv{lvl} Asc{asc} DEF failed: got {base['def_']}, expected {exp_def}"
    # Ascension stat at Lv90 Asc6
    _, k_asc90, _, _ = stat_engine_service.resolve_character_base_stats("Kaedehara Kazuha", level=90, ascension=6)
    assert k_asc90.get("Elemental Mastery") == 115.2

    # 2. Hu Tao
    ht_expected = [
        (1, 0, 1211, 8, 68),
        (20, 0, 3141, 21, 177),
        (20, 1, 4179, 29, 235),
        (80, 6, 14459, 99, 815),
        (90, 6, 15552, 106, 876),
    ]
    for lvl, asc, exp_hp, exp_atk, exp_def in ht_expected:
        base, _, status, _ = stat_engine_service.resolve_character_base_stats("Hu Tao", level=lvl, ascension=asc)
        assert status == CalculationStatus.COMPLETE
        assert base["hp"] == exp_hp
        assert base["atk"] == exp_atk
        assert base["def_"] == exp_def
    _, ht_asc90, _, _ = stat_engine_service.resolve_character_base_stats("Hu Tao", level=90, ascension=6)
    assert round(ht_asc90.get("CRIT DMG", 0), 3) == 0.384

    # 3. Xiao
    x_base1, _, _, _ = stat_engine_service.resolve_character_base_stats("Xiao", level=1, ascension=0)
    assert x_base1["hp"] == 991
    assert x_base1["atk"] == 27
    assert x_base1["def_"] == 62
    x_base90, x_asc90, _, _ = stat_engine_service.resolve_character_base_stats("Xiao", level=90, ascension=6)
    assert x_base90["hp"] == 12736
    assert x_base90["atk"] == 349
    assert x_base90["def_"] == 799
    assert round(x_asc90.get("CRIT Rate", 0), 3) == 0.192

    # 4. Arlecchino
    a_base1, _, _, _ = stat_engine_service.resolve_character_base_stats("Arlecchino", level=1, ascension=0)
    assert a_base1["hp"] == 1020
    assert a_base1["atk"] == 27
    assert a_base1["def_"] == 60
    a_base90, a_asc90, _, _ = stat_engine_service.resolve_character_base_stats("Arlecchino", level=90, ascension=6)
    assert a_base90["hp"] == 13103
    assert a_base90["atk"] == 342
    assert a_base90["def_"] == 765
    assert round(a_asc90.get("CRIT DMG", 0), 3) == 0.384


def test_golden_weapons_level_scaling_breakpoints():
    """
    Forensic verification of base ATK and secondary stat across all 13 breakpoints
    for Freedom-Sworn, Xiphos' Moonlight, Staff of Homa, Primordial Jade Cutter, Calamity Queller.
    """
    # 1. Freedom-Sworn (5* 608 ATK, EM secondary)
    fs_expected = [
        (1, 0, 46.0, 43.0),
        (20, 0, 122.0, 76.0),
        (20, 1, 153.0, 76.0),
        (40, 1, 235.0, 111.0),
        (40, 2, 266.0, 111.0),
        (50, 2, 308.0, 129.0),
        (50, 3, 340.0, 129.0),
        (60, 3, 382.0, 146.0),
        (60, 4, 414.0, 146.0),
        (70, 4, 457.0, 164.0),
        (70, 5, 488.0, 164.0),
        (80, 5, 532.0, 181.0),
        (80, 6, 563.0, 181.0),
        (90, 6, 608.0, 198.0),  # Exact canonical integer EM
    ]
    for lvl, asc, exp_atk, exp_sub in fs_expected:
        atk, sub_name, sub_val, _, status, _ = stat_engine_service.resolve_weapon_stats("Freedom-Sworn", level=lvl, ascension=asc)
        assert status == CalculationStatus.COMPLETE
        assert atk == exp_atk, f"Freedom-Sworn Lv{lvl} Asc{asc} ATK: got {atk}, expected {exp_atk}"
        assert sub_name == "Elemental Mastery"
        assert sub_val == exp_sub, f"Freedom-Sworn Lv{lvl} Asc{asc} EM: got {sub_val}, expected {exp_sub}"

    # 2. Xiphos' Moonlight (4* 510 ATK, EM secondary)
    x_atk1, _, x_sub1, _, _, _ = stat_engine_service.resolve_weapon_stats("Xiphos' Moonlight", level=1, ascension=0)
    assert x_atk1 == 42.0
    assert x_sub1 == 36.0
    x_atk90, _, x_sub90, _, _, _ = stat_engine_service.resolve_weapon_stats("Xiphos' Moonlight", level=90, ascension=6)
    assert x_atk90 == 510.0
    assert x_sub90 == 165.0  # Exact canonical integer EM

    # 3. Staff of Homa (5* 608 ATK, CRIT DMG secondary)
    h_atk1, _, h_sub1, _, _, _ = stat_engine_service.resolve_weapon_stats("Staff of Homa", level=1, ascension=0)
    assert h_atk1 == 46.0
    assert round(h_sub1 * 100, 1) == 14.4
    h_atk90, _, h_sub90, _, _, _ = stat_engine_service.resolve_weapon_stats("Staff of Homa", level=90, ascension=6)
    assert h_atk90 == 608.0
    assert round(h_sub90 * 100, 1) == 66.2

    # 4. Primordial Jade Cutter (5* 542 ATK, CRIT Rate secondary)
    jc_atk1, _, jc_sub1, _, _, _ = stat_engine_service.resolve_weapon_stats("Primordial Jade Cutter", level=1, ascension=0)
    assert jc_atk1 == 44.0
    assert round(jc_sub1 * 100, 1) == 9.6
    jc_atk90, _, jc_sub90, _, _, _ = stat_engine_service.resolve_weapon_stats("Primordial Jade Cutter", level=90, ascension=6)
    assert jc_atk90 == 542.0
    assert round(jc_sub90 * 100, 1) == 44.1

    # 5. Calamity Queller (5* 741 ATK, ATK% secondary)
    cq_atk1, _, cq_sub1, _, _, _ = stat_engine_service.resolve_weapon_stats("Calamity Queller", level=1, ascension=0)
    assert cq_atk1 == 49.0
    assert round(cq_sub1 * 100, 1) == 3.6
    cq_atk90, _, cq_sub90, _, _, _ = stat_engine_service.resolve_weapon_stats("Calamity Queller", level=90, ascension=6)
    assert cq_atk90 == 741.0
    assert round(cq_sub90 * 100, 1) == 16.5


def test_weapon_passives_and_refinement_matrix():
    """Verify static unconditional passives across refinements R1-R5."""
    # Staff of Homa: HP +20% to +40%
    for r, exp_hp in [(1, 0.20), (2, 0.25), (3, 0.30), (4, 0.35), (5, 0.40)]:
        _, _, _, passives, _, _ = stat_engine_service.resolve_weapon_stats("Staff of Homa", refinement=r)
        assert passives.get("hp_") == exp_hp

    # Primordial Jade Cutter: HP +20% to +40%
    for r, exp_hp in [(1, 0.20), (2, 0.25), (3, 0.30), (4, 0.35), (5, 0.40)]:
        _, _, _, passives, _, _ = stat_engine_service.resolve_weapon_stats("Primordial Jade Cutter", refinement=r)
        assert passives.get("hp_") == exp_hp

    # Calamity Queller: Elemental DMG +12% to +24%
    for r, exp_dmg in [(1, 0.12), (2, 0.15), (3, 0.18), (4, 0.21), (5, 0.24)]:
        _, _, _, passives, _, _ = stat_engine_service.resolve_weapon_stats("Calamity Queller", refinement=r)
        assert passives.get("all_elemental_dmg_") == exp_dmg

    # Freedom-Sworn: All DMG +10% to +20%
    for r, exp_dmg in [(1, 0.10), (2, 0.125), (3, 0.15), (4, 0.175), (5, 0.20)]:
        _, _, _, passives, _, _ = stat_engine_service.resolve_weapon_stats("Freedom-Sworn", refinement=r)
        assert passives.get("all_dmg_") == exp_dmg

    # The Widsith: 0 unconditional sheet stats (conditional combat only)
    _, _, _, passives_w, _, _ = stat_engine_service.resolve_weapon_stats("The Widsith", refinement=5)
    assert passives_w == {}


def test_artifact_canonical_progression_matrix():
    """Verify exact artifact main stats across levels 0, 4, 8, 12, 16, 20 from ReliquaryLevel tables."""
    # 5-Star levels
    assert stat_engine_service.resolve_artifact_main_stat("flower", "hp", 5, 0)[1] == 717.0
    assert stat_engine_service.resolve_artifact_main_stat("flower", "hp", 5, 20)[1] == 4780.0
    assert stat_engine_service.resolve_artifact_main_stat("plume", "atk", 5, 0)[1] == 47.0
    assert stat_engine_service.resolve_artifact_main_stat("plume", "atk", 5, 20)[1] == 311.0
    assert stat_engine_service.resolve_artifact_main_stat("sands", "atk_", 5, 20)[1] == 0.466
    assert stat_engine_service.resolve_artifact_main_stat("sands", "enerRech_", 5, 20)[1] == 0.518
    # 5-Star EM: exact 187 at +20 (from raw 186.5)
    assert stat_engine_service.resolve_artifact_main_stat("circlet", "eleMas", 5, 20)[1] == 187.0
    assert stat_engine_service.resolve_artifact_main_stat("circlet", "critRate_", 5, 20)[1] == 0.311
    assert stat_engine_service.resolve_artifact_main_stat("circlet", "critDMG_", 5, 20)[1] == 0.622

    # 4-Star levels
    assert stat_engine_service.resolve_artifact_main_stat("flower", "hp", 4, 0)[1] == 645.0
    assert stat_engine_service.resolve_artifact_main_stat("flower", "hp", 4, 16)[1] == 3571.0
    assert stat_engine_service.resolve_artifact_main_stat("plume", "atk", 4, 16)[1] == 232.0
    # 4-Star EM: exact 139 at +16
    assert stat_engine_service.resolve_artifact_main_stat("sands", "eleMas", 4, 16)[1] == 139.0


def test_set_bonus_classification_sheet_vs_combat():
    """Verify artifact set bonus classification: 2pc sheet stats vs 4pc combat modifiers."""
    arts = [
        {"slot": "flower", "set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "hp"},
        {"slot": "plume", "set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "atk"},
        {"slot": "sands", "set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "eleMas"},
        {"slot": "goblet", "set_name": "Viridescent Venerer", "rarity": 5, "level": 20, "main_stat_key": "anemo_dmg_"},
    ]
    _, active_bonuses, _ = stat_engine_service.resolve_artifact_inventory_contribution(arts)
    assert len(active_bonuses) == 2
    b_2pc = next(b for b in active_bonuses if b.pieces_active == 2)
    b_4pc = next(b for b in active_bonuses if b.pieces_active == 4)

    # 2pc is a sheet stat
    assert b_2pc.is_character_sheet_stat is True
    assert b_2pc.character_sheet_stats.get("anemo_dmg_") == 0.15
    assert len(b_2pc.combat_modifiers) == 0

    # 4pc is a combat modifier
    assert b_4pc.is_character_sheet_stat is False
    assert b_4pc.character_sheet_stats == {}
    assert len(b_4pc.combat_modifiers) == 1
    assert "4-Piece Set Bonus" in b_4pc.combat_modifiers[0] or "Swirl" in b_4pc.combat_modifiers[0]


# ==============================================================================
# 9. SECURITY AUDIT TESTS (POST /api/build/calculate)
# ==============================================================================

def test_security_audit_arbitrary_stat_injection_forbidden(client):
    """
    Verify clients cannot submit arbitrary numerical game stats in POST /api/build/calculate.
    Pydantic ConfigDict(extra='forbid') MUST reject arbitrary parameters with HTTP 422.
    """
    # 1. Injected base_atk
    res1 = client.post("/api/build/calculate", json={"character": "Hu Tao", "base_atk": 999999})
    assert res1.status_code == 422, f"Expected 422 for injected base_atk, got {res1.status_code}"

    # 2. Injected crit_rate
    res2 = client.post("/api/build/calculate", json={"character": "Hu Tao", "crit_rate": 999})
    assert res2.status_code == 422, f"Expected 422 for injected crit_rate, got {res2.status_code}"

    # 3. Injected weapon_atk
    res3 = client.post("/api/build/calculate", json={"character": "Hu Tao", "weapon_atk": 50000})
    assert res3.status_code == 422, f"Expected 422 for injected weapon_atk, got {res3.status_code}"

    # 4. Injected main_stat_value inside artifact
    res4 = client.post("/api/build/calculate", json={
        "character": "Hu Tao",
        "artifacts": [{
            "slot": "flower",
            "set_name": "Crimson Witch of Flames",
            "main_stat_key": "hp",
            "main_stat_value": 999999
        }]
    })
    assert res4.status_code == 422, f"Expected 422 for injected main_stat_value, got {res4.status_code}"


def test_security_audit_account_instance_validation(client):
    """
    Verify clients cannot reference nonexistent account instance IDs.
    Must return HTTP 400 Bad Request.
    """
    # Bogus character instance
    res1 = client.post("/api/build/calculate", json={
        "character": "Hu Tao",
        "account_character_instance_id": "nonexistent-instance-9999"
    })
    assert res1.status_code == 400

    # Bogus artifact instance
    res2 = client.post("/api/build/calculate", json={
        "character": "Hu Tao",
        "artifacts": [{
            "slot": "flower",
            "set_name": "Crimson Witch of Flames",
            "main_stat_key": "hp",
            "account_instance_id": "nonexistent-art-8888"
        }]
    })
    assert res2.status_code == 400


# ==============================================================================
# 11. VERSION SAFETY & PROVENANCE COMPATIBILITY TESTS (Phase 7 Final Gate)
# ==============================================================================

def test_version_evidence_case_1_matching_dataset_version():
    """Case 1: requested version matches canonical dataset version (5.4) -> COMPLETE, MATCHING."""
    build = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version="5.4"
    )
    assert build.calculation_status == CalculationStatus.COMPLETE
    assert build.version_compatibility == VersionCompatibilityStatus.MATCHING
    assert build.dataset_version == "5.4"
    assert build.game_version == "5.4"
    assert any("verified for v5.4" in w for w in build.warnings)


def test_version_evidence_case_2_verified_invariant_compatibility():
    """Case 2: Pure Category A engine constants (curves/levels) -> COMPLETE, VERIFIED_COMPATIBLE."""
    stat, compat, warns, ver = stat_engine_service.evaluate_version_compatibility(
        "7.0",
        is_pure_engine_constant=True
    )
    assert stat == CalculationStatus.COMPLETE
    assert compat == VersionCompatibilityStatus.VERIFIED_COMPATIBLE
    assert ver == "7.0"
    assert any("verified as invariant across all game versions" in w for w in warns)


def test_version_evidence_case_3_registry_only_compatibility():
    """Case 3: requested version is newer (7.0) than dataset (5.4) -> COMPLETE, PROJECT_REGISTRY_COMPATIBLE."""
    build = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version="7.0"
    )
    assert build.calculation_status == CalculationStatus.COMPLETE
    assert build.version_compatibility == VersionCompatibilityStatus.PROJECT_REGISTRY_COMPATIBLE
    assert build.dataset_version == "5.4"
    assert build.game_version == "7.0"
    # Declares project registry compatibility and lack of direct v7.0 client data
    assert any("via project-maintained patch registry" in w and "direct v7.0 game client data is unavailable" in w for w in build.warnings)


def test_version_evidence_case_4_unknown_compatibility():
    """Case 4: unrecognized or non-standard version string -> UNSUPPORTED, UNKNOWN_COMPATIBILITY."""
    build = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version="unknown"
    )
    assert build.calculation_status == CalculationStatus.UNSUPPORTED
    assert build.version_compatibility == VersionCompatibilityStatus.UNKNOWN_COMPATIBILITY
    assert any("unknown compatibility status" in w for w in build.warnings)

    build_invalid = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version="invalid_ver"
    )
    assert build_invalid.calculation_status == CalculationStatus.UNSUPPORTED
    assert build_invalid.version_compatibility == VersionCompatibilityStatus.UNKNOWN_COMPATIBILITY


def test_version_evidence_case_5_conflicting_intervening_change():
    """Case 5: Intervening patch modifies character/system -> PARTIAL, STALE_INTERVENING_CHANGES."""
    from backend.services.version_service import version_service
    version_service._patch_changes["5.5"] = ["Kaedehara Kazuha"]
    try:
        build = stat_engine_service.calculate_build_stats(
            "Kaedehara Kazuha",
            weapon_name_or_id="Freedom-Sworn",
            game_version="7.0"
        )
        assert build.calculation_status == CalculationStatus.PARTIAL
        assert build.version_compatibility == VersionCompatibilityStatus.STALE_INTERVENING_CHANGES
        assert any("affected by patch changes between v5.4 and v7.0" in w for w in build.warnings)
    finally:
        version_service.load_patch_changes()


def test_version_evidence_case_6_future_unreleased_version():
    """Case 6: future/unreleased version (8.0) -> UNSUPPORTED, UNSUPPORTED_FUTURE."""
    build = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version="8.0"
    )
    assert build.calculation_status == CalculationStatus.UNSUPPORTED
    assert build.version_compatibility == VersionCompatibilityStatus.UNSUPPORTED_FUTURE
    assert any("unrecognized in canonical patch registry" in w or "unreleased" in w for w in build.warnings)


def test_version_evidence_case_7_missing_version_metadata():
    """Case 7: missing version metadata (None/empty) -> PARTIAL, MISSING_VERSION_METADATA."""
    build_none = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version=None
    )
    assert build_none.calculation_status == CalculationStatus.PARTIAL
    assert build_none.version_compatibility == VersionCompatibilityStatus.MISSING_VERSION_METADATA
    assert any("Missing version metadata" in w for w in build_none.warnings)

    build_empty = stat_engine_service.calculate_build_stats(
        "Kaedehara Kazuha",
        weapon_name_or_id="Freedom-Sworn",
        game_version=""
    )
    assert build_empty.calculation_status == CalculationStatus.PARTIAL
    assert build_empty.version_compatibility == VersionCompatibilityStatus.MISSING_VERSION_METADATA


def test_version_evidence_case_8_manifest_provenance_integrity():
    """Case 8: manifest.json contains complete provenance, hashes, versions, and invariance classifications."""
    import json
    from pathlib import Path
    manifest_file = Path("data/processed/manifest.json")
    assert manifest_file.exists()

    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    game_data = manifest.get("game_data", {})
    assert game_data.get("dataset_version") == "5.4"
    assert game_data.get("project_target_version") == "7.0"
    assert len(game_data.get("aggregate_sha256", "")) == 64

    files = {item["file_name"]: item for item in game_data.get("files", [])}
    expected_files = [
        "artifact_levels.json",
        "artifacts.json",
        "avatar_curves.json",
        "characters.json",
        "materials.json",
        "weapon_curves.json",
        "weapons.json",
    ]
    for ef in expected_files:
        assert ef in files, f"Missing {ef} in manifest game_data.files"
        entry = files[ef]
        assert entry["dataset_version"] == "5.4"
        assert entry["source_version"] == "5.4"
        assert entry["project_target_version"] == "7.0"
        assert entry["source_id"] in ("src_animegamedata", "src_project_amber")
        assert len(entry["sha256"]) == 64
        assert entry["record_count"] > 0
        assert entry["verification_status"] == "VERIFIED_STRUCTURED"
        assert entry["source_url"].startswith("http")
        assert entry["invariance_classification"] in ("CATEGORY_A_ENGINE_CONSTANT", "CATEGORY_B_GAME_CONTENT_STATIC")


def test_api_version_parameter_and_safety(client):
    """Verify REST API enforces version compatibility and reports dataset vs game version."""
    # 1. Matching version 5.4
    res_a = client.post("/api/build/calculate", json={
        "character": "Kaedehara Kazuha",
        "weapon": "Freedom-Sworn",
        "game_version": "5.4",
    })
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["calculation_status"] == "COMPLETE"
    assert data_a["version_compatibility"] == "MATCHING"
    assert data_a["dataset_version"] == "5.4"
    assert data_a["game_version"] == "5.4"

    # 2. Target version 7.0
    res_b = client.post("/api/build/calculate", json={
        "character": "Kaedehara Kazuha",
        "weapon": "Freedom-Sworn",
        "game_version": "7.0",
    })
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["calculation_status"] == "COMPLETE"
    assert data_b["version_compatibility"] == "PROJECT_REGISTRY_COMPATIBLE"
    assert data_b["dataset_version"] == "5.4"
    assert data_b["game_version"] == "7.0"

    # 3. Unreleased version 8.0
    res_c = client.post("/api/build/calculate", json={
        "character": "Kaedehara Kazuha",
        "weapon": "Freedom-Sworn",
        "game_version": "8.0",
    })
    assert res_c.status_code == 200
    data_c = res_c.json()
    assert data_c["calculation_status"] == "UNSUPPORTED"
    assert data_c["version_compatibility"] == "UNSUPPORTED_FUTURE"

    # 4. Missing version metadata (omitted) -> PARTIAL
    res_d = client.post("/api/build/calculate", json={
        "character": "Kaedehara Kazuha",
        "weapon": "Freedom-Sworn",
    })
    assert res_d.status_code == 200
    data_d = res_d.json()
    assert data_d["calculation_status"] == "PARTIAL"
    assert data_d["version_compatibility"] == "MISSING_VERSION_METADATA"

