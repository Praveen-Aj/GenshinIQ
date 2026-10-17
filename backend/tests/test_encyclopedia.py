"""
Phase 11.1 — Forensic Remediation Test Suite for Characters, Weapons, Artifacts, Materials & Account Integration.

Enforces:
1. Exact canonical base stats and curves (zero loose bounds).
2. Level and ascension boundary transitions (Lv 20 A0 vs A1, Lv 40 A1 vs A2).
3. Negative tests: 404 Not Found for unknown entities; 422 Unprocessable for out-of-bounds parameters.
4. Exact weapon refinement scaling (R1 vs R5) and passives.
5. Exact artifact set bonuses and piece identity.
6. Artifact recommendation contract: `set_name` present, non-empty, contract agreements, zero "undefined".
7. Material resolution: zero raw numeric IDs in character materials, Sea Ganoderma (101206) resolved.
8. Guide classification: CURATED_CHARACTER_GUIDE vs GENERIC_FALLBACK distinction.
9. Account inventory vs showcase ownership semantics (GOOD v3 + Enka).
"""

import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.encyclopedia_service import encyclopedia_service
from backend.services.game_data_service import game_data_service
from backend.services.account_inventory_service import account_inventory_service

client = TestClient(app)


# ==============================================================================
# 1. EXACT CANONICAL CHARACTER SCALING & BOUNDARIES
# ==============================================================================

def test_character_exact_scaling_canonical():
    """Verify exact canonical base stats derived from raw curves (no loose bounds)."""
    # 1. Kaedehara Kazuha (5-star Anemo Sword)
    kz_20 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=20, ascension=0)
    assert kz_20["level"] == 20
    assert kz_20["ascension"] == 0
    assert kz_20["base_hp"] == 2695.0
    assert kz_20["base_atk"] == 60.0
    assert kz_20["base_def"] == 163.0

    kz_90 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=90, ascension=6)
    assert kz_90["level"] == 90
    assert kz_90["ascension"] == 6
    assert kz_90["base_hp"] == 13348.0
    assert kz_90["base_atk"] == 297.0
    assert kz_90["base_def"] == 807.0
    assert kz_90["ascension_stats"].get("Elemental Mastery") == 115.2

    # 2. Furina (5-star Hydro Sword)
    fu_90 = encyclopedia_service.get_character_scaling("Furina", level=90, ascension=6)
    assert fu_90["base_hp"] == 15307.0
    assert fu_90["base_atk"] == 244.0
    assert fu_90["base_def"] == 696.0
    assert fu_90["ascension_stats"].get("CRIT Rate") == 0.192

    # 3. Arlecchino (5-star Pyro Polearm)
    arl_90 = encyclopedia_service.get_character_scaling("Arlecchino", level=90, ascension=6)
    assert arl_90["base_hp"] == 13103.0
    assert arl_90["base_atk"] == 342.0
    assert arl_90["base_def"] == 765.0
    assert arl_90["ascension_stats"].get("CRIT DMG") == 0.384

    # 4. Mavuika (5-star Pyro Claymore)
    mav_90 = encyclopedia_service.get_character_scaling("Mavuika", level=90, ascension=6)
    assert mav_90["base_hp"] == 12552.0
    assert mav_90["base_atk"] == 359.0
    assert mav_90["base_def"] == 792.0
    assert mav_90["ascension_stats"].get("CRIT DMG") == 0.384


def test_character_ascension_boundary_transitions():
    """Verify sudden stat jump on exact ascension boundary."""
    # Lv 20 unascended vs ascended
    kz_a0 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=20, ascension=0)
    kz_a1 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=20, ascension=1)
    assert kz_a0["base_hp"] == 2695.0
    assert kz_a1["base_hp"] == 3586.0
    assert kz_a1["base_hp"] > kz_a0["base_hp"]

    # Lv 40 A1 vs A2
    kz_40_a1 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=40, ascension=1)
    kz_40_a2 = encyclopedia_service.get_character_scaling("Kaedehara Kazuha", level=40, ascension=2)
    assert kz_40_a1["base_hp"] == 5366.0
    assert kz_40_a2["base_hp"] == 5999.0


def test_character_negative_and_validation():
    """Verify fail-closed 404 on nonexistent characters and 422 on invalid parameters."""
    # Nonexistent character -> 404
    res_404 = client.get("/api/data/characters/nonexistent_character_xyz/scaling")
    assert res_404.status_code == 404

    # Invalid levels -> 422
    res_lvl0 = client.get("/api/data/characters/kaedehara_kazuha/scaling?level=0")
    assert res_lvl0.status_code == 422
    res_lvl91 = client.get("/api/data/characters/kaedehara_kazuha/scaling?level=91")
    assert res_lvl91.status_code == 422

    # Invalid ascensions -> 422
    res_asc_neg = client.get("/api/data/characters/kaedehara_kazuha/scaling?level=90&ascension=-1")
    assert res_asc_neg.status_code == 422
    res_asc_high = client.get("/api/data/characters/kaedehara_kazuha/scaling?level=90&ascension=7")
    assert res_asc_high.status_code == 422


# ==============================================================================
# 2. EXACT CANONICAL WEAPON SCALING & REFINEMENT
# ==============================================================================

def test_weapon_exact_scaling_canonical():
    """Verify exact canonical weapon base ATK, substats, and refinement passive values."""
    # 1. Mistsplitter Reforged (5-star Sword)
    mis_r1 = encyclopedia_service.get_weapon_scaling("Mistsplitter Reforged", level=90, refinement=1)
    assert mis_r1["base_atk"] == 674.0
    assert mis_r1["sub_stat_type"] == "CRIT DMG"
    assert mis_r1["sub_stat_formatted"] == "44.1%"
    assert mis_r1["static_passives"].get("all_elemental_dmg_") == 0.12

    mis_r5 = encyclopedia_service.get_weapon_scaling("Mistsplitter Reforged", level=90, refinement=5)
    assert mis_r5["base_atk"] == 674.0
    assert mis_r5["static_passives"].get("all_elemental_dmg_") == 0.24

    # 2. Freedom-Sworn (5-star Sword)
    fs_r1 = encyclopedia_service.get_weapon_scaling("Freedom-Sworn", level=90, refinement=1)
    assert fs_r1["base_atk"] == 608.0
    assert fs_r1["sub_stat_type"] == "Elemental Mastery"
    assert fs_r1["sub_stat_formatted"] == "198"
    assert fs_r1["static_passives"].get("all_dmg_") == 0.10

    fs_r5 = encyclopedia_service.get_weapon_scaling("Freedom-Sworn", level=90, refinement=5)
    assert fs_r5["base_atk"] == 608.0
    assert fs_r5["static_passives"].get("all_dmg_") == 0.20

    # 3. Iron Sting (4-star Craftable Sword)
    st_r1 = encyclopedia_service.get_weapon_scaling("Iron Sting", level=90, refinement=1)
    assert st_r1["base_atk"] == 510.0
    assert st_r1["sub_stat_formatted"] == "165"


def test_weapon_negative_and_validation():
    """Verify fail-closed 404 on nonexistent weapons and 422 on invalid parameters."""
    res_404 = client.get("/api/data/weapons/nonexistent_weapon_xyz/scaling")
    assert res_404.status_code == 404

    # Invalid level
    res_lvl0 = client.get("/api/data/weapons/mistsplitter_reforged/scaling?level=0")
    assert res_lvl0.status_code == 422
    res_lvl91 = client.get("/api/data/weapons/mistsplitter_reforged/scaling?level=91")
    assert res_lvl91.status_code == 422

    # Invalid refinement
    res_r0 = client.get("/api/data/weapons/mistsplitter_reforged/scaling?level=90&refinement=0")
    assert res_r0.status_code == 422
    res_r6 = client.get("/api/data/weapons/mistsplitter_reforged/scaling?level=90&refinement=6")
    assert res_r6.status_code == 422


# ==============================================================================
# 3. CANONICAL ARTIFACT SETS & RECOMMENDATION CONTRACT (CRITICAL FIX 1)
# ==============================================================================

def test_artifact_sets_endpoint_and_exact_bonuses():
    """Verify canonical artifact sets endpoint returns exact 2pc and 4pc bonus mechanics."""
    res = client.get("/api/data/artifacts/viridescent_venerer")
    assert res.status_code == 200
    art = res.json()
    assert art["name"] == "Viridescent Venerer"
    assert "15%" in art["bonus_2pc"]
    assert "60%" in art["bonus_4pc"]
    assert "40%" in art["bonus_4pc"]
    assert len(art["pieces"]) == 5

    res_404 = client.get("/api/data/artifacts/nonexistent_set_xyz")
    assert res_404.status_code == 404


def test_artifact_recommendation_contract_no_undefined():
    """Verify recommended artifacts contract: set_name non-empty and no 'undefined' across multiple characters."""
    sample_characters = [
        "Kaedehara Kazuha", "Furina", "Arlecchino", "Bennett", "Xiangling", "Amber"
    ]
    for c_name in sample_characters:
        guide = encyclopedia_service.get_character_build_guide(c_name)
        assert guide is not None
        rec_arts = guide.get("recommended_artifacts", [])
        assert len(rec_arts) >= 1, f"Character {c_name} must have at least 1 recommended artifact set."

        for art in rec_arts:
            assert "set_name" in art, f"Missing 'set_name' in {art} for {c_name}"
            assert art["set_name"], f"'set_name' must not be empty in {art} for {c_name}"
            assert art["set_name"] != "undefined", f"Literal 'undefined' found in set_name for {c_name}"
            assert "name" in art
            assert art["name"] == art["set_name"]
            assert art["pieces"] in [2, 4]
            assert "notes" in art and len(art["notes"]) > 0


# ==============================================================================
# 4. MATERIALS RESOLUTION (CRITICAL FIX 2)
# ==============================================================================

def test_materials_resolution_no_raw_numeric_ids():
    """Verify all character ascension materials are resolved to canonical names (zero numeric IDs)."""
    # 1. Kaedehara Kazuha
    kz = game_data_service.get_character("Kaedehara Kazuha")
    assert kz is not None
    assert "Sea Ganoderma" in kz.ascension_materials
    assert "101206" not in kz.ascension_materials
    assert not any(str(m).isdigit() for m in kz.ascension_materials)

    # 2. Furina
    fu = game_data_service.get_character("Furina")
    assert fu is not None
    assert "Lakelight Lily" in fu.ascension_materials
    assert "101238" not in fu.ascension_materials
    assert not any(str(m).isdigit() for m in fu.ascension_materials)

    # 3. Arlecchino
    arl = game_data_service.get_character("Arlecchino")
    assert arl is not None
    assert "Rainbow Rose" in arl.ascension_materials
    assert "101236" not in arl.ascension_materials
    assert not any(str(m).isdigit() for m in arl.ascension_materials)

    # 4. Global integrity check across all 121 characters
    all_chars = game_data_service.list_characters()
    assert len(all_chars) >= 120
    for char in all_chars:
        for m in char.ascension_materials:
            assert not str(m).isdigit(), f"Raw numeric ID '{m}' found in ascension materials for {char.name}"
        for m in char.talent_materials:
            assert not str(m).isdigit(), f"Raw numeric ID '{m}' found in talent materials for {char.name}"

    # 5. Materials API Endpoint includes Sea Ganoderma
    res = client.get("/api/data/materials")
    assert res.status_code == 200
    mats = res.json()
    sg = next((m for m in mats if m["name"] == "Sea Ganoderma"), None)
    assert sg is not None
    assert sg["id"] == 101206
    assert sg["type"] == "Local Specialty"


# ==============================================================================
# 5. GUIDE CLASSIFICATION & PROVENANCE (FINDING 4)
# ==============================================================================

def test_guide_classification_and_provenance():
    """Verify explicit classification between curated guides and generic fallback templates."""
    # Curated characters
    for c_name in ["Kaedehara Kazuha", "Furina", "Arlecchino", "Bennett"]:
        guide = encyclopedia_service.get_character_build_guide(c_name)
        assert guide["guide_type"] == "CURATED_CHARACTER_GUIDE", f"{c_name} must be CURATED_CHARACTER_GUIDE"
        assert "KeqingMains" in guide["guide_provenance"]

    # Non-curated character (fallback template)
    guide_fallback = encyclopedia_service.get_character_build_guide("Amber")
    assert guide_fallback["guide_type"] == "GENERIC_FALLBACK"
    assert "Baseline Archetype" in guide_fallback["guide_provenance"]

    # Unknown character -> 404 via API
    res_404 = client.get("/api/data/characters/unknown_char_xyz/guide")
    assert res_404.status_code == 404


# ==============================================================================
# 6. ACCOUNT INVENTORY INTEGRATION SEMANTICS (FINDING 5)
# ==============================================================================

def test_account_inventory_and_showcase_semantics():
    """Verify GOOD v3 inventory ownership, showcase distinction, and multi-weapon semantics."""
    snap = account_inventory_service.get_active_snapshot()
    assert snap is not None
    assert len(snap.characters) > 0
    assert len(snap.weapons) > 0

    # 1. Owned character in GOOD inventory
    good_char = snap.characters[0]
    assert good_char.canonical_name
    assert good_char.level >= 1
    assert 0 <= good_char.constellation <= 6

    # 2. Multiple copies of same weapon preserve distinct account_instance_ids
    wep_by_name = {}
    for w in snap.weapons:
        wep_by_name.setdefault(w.canonical_name, []).append(w)
    multi_weps = [copies for copies in wep_by_name.values() if len(copies) > 1]
    assert len(multi_weps) > 0, "Account must contain legitimate multi-copy weapons"
    sample_multi = multi_weps[0]
    instance_ids = [w.account_instance_id for w in sample_multi]
    assert len(instance_ids) == len(set(instance_ids)), "Every weapon copy must have unique instance ID"

    # 3. Equipped weapon resolution
    equipped_weps = [w for w in snap.weapons if w.location]
    assert len(equipped_weps) > 0
    sample_eq = equipped_weps[0]
    assert sample_eq.location
    assert sample_eq.level >= 1
    assert 1 <= sample_eq.refinement <= 5

    # 4. Artifact inventory
    assert len(snap.artifacts) > 0
    sample_art = snap.artifacts[0]
    assert sample_art.canonical_set_name
    assert sample_art.slot in ["flower", "plume", "sands", "goblet", "circlet"]

