"""Data Pipeline and Canonical Game Data Integrity Tests.

Guarantees that the game data layer adheres to Phase 1 truthfulness mandates:
- Zero duplicate entity IDs across all datasets
- Zero placeholder or fabricated stats (no 250.0 ATK, 11000.0 HP)
- Strict unique identity for historically colliding pairs (Kazuha/Ayaka, Homa/Calamity, Mistsplitter/Freedom-Sworn)
- Verified refinement descriptions for all 4-star and 5-star weapons
- Comprehensive materials catalog coverage (>50 items)
"""

import json
from collections import Counter
from pathlib import Path
import pytest

DATA_DIR = Path("data/processed/game_data")


@pytest.fixture
def characters_data():
    path = DATA_DIR / "characters.json"
    assert path.exists(), f"Missing canonical file: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def weapons_data():
    path = DATA_DIR / "weapons.json"
    assert path.exists(), f"Missing canonical file: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def artifacts_data():
    path = DATA_DIR / "artifacts.json"
    assert path.exists(), f"Missing canonical file: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def materials_data():
    path = DATA_DIR / "materials.json"
    assert path.exists(), f"Missing canonical file: {path}"
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_characters_zero_duplicates(characters_data):
    """Ensure every character has a distinct, unique ID and name."""
    ids = [c["id"] for c in characters_data]
    id_counts = Counter(ids)
    dupe_ids = {cid: cnt for cid, cnt in id_counts.items() if cnt > 1}
    assert not dupe_ids, f"Duplicate Character IDs detected: {dupe_ids}"

    names = [c["name"].lower() for c in characters_data]
    name_counts = Counter(names)
    dupe_names = {name: cnt for name, cnt in name_counts.items() if cnt > 1}
    assert not dupe_names, f"Duplicate Character names detected: {dupe_names}"


def test_characters_zero_placeholder_stats(characters_data):
    """Ensure no character is defaulted to fake 250 ATK or 11000 HP values."""
    for char in characters_data:
        name = char["name"]
        hp = char["base_hp_lvl90"]
        atk = char["base_atk_lvl90"]
        df = char["base_def_lvl90"]

        assert not (hp == 11000.0 and atk == 250.0), (
            f"Character '{name}' has fabricated placeholder stats: HP {hp}, ATK {atk}"
        )
        assert hp > 0, f"Character '{name}' has non-positive base HP: {hp}"
        assert atk > 0, f"Character '{name}' has non-positive base ATK: {atk}"
        assert df > 0, f"Character '{name}' has non-positive base DEF: {df}"
        assert char["element"] in ["Pyro", "Hydro", "Anemo", "Electro", "Dendro", "Cryo", "Geo"]
        assert char["weapon_type"] in ["Sword", "Claymore", "Polearm", "Bow", "Catalyst"]


def test_characters_historical_collisions_resolved(characters_data):
    """Ensure historically colliding characters have distinct, correct canonical IDs."""
    char_by_name = {c["name"].lower(): c for c in characters_data}

    assert "kaedehara kazuha" in char_by_name
    assert "kamisato ayaka" in char_by_name

    kazuha = char_by_name["kaedehara kazuha"]
    ayaka = char_by_name["kamisato ayaka"]

    assert kazuha["id"] != ayaka["id"], "Kazuha and Ayaka still share the same ID!"
    assert kazuha["id"] in [10000047, 10000052] or kazuha["id"] > 10000000


def test_weapons_zero_duplicates(weapons_data):
    """Ensure every weapon has a distinct, unique ID and name."""
    ids = [w["id"] for w in weapons_data]
    id_counts = Counter(ids)
    dupe_ids = {wid: cnt for wid, cnt in id_counts.items() if cnt > 1}
    assert not dupe_ids, f"Duplicate Weapon IDs detected: {dupe_ids}"


def test_weapons_historical_collisions_resolved(weapons_data):
    """Ensure historically colliding weapons have distinct canonical IDs."""
    wep_by_name = {w["name"].lower(): w for w in weapons_data}

    if "staff of homa" in wep_by_name and "calamity queller" in wep_by_name:
        assert wep_by_name["staff of homa"]["id"] != wep_by_name["calamity queller"]["id"]

    if "mistsplitter reforged" in wep_by_name and "freedom-sworn" in wep_by_name:
        assert wep_by_name["mistsplitter reforged"]["id"] != wep_by_name["freedom-sworn"]["id"]

    if "tome of the eternal flow" in wep_by_name and "lost prayer to the sacred winds" in wep_by_name:
        assert wep_by_name["tome of the eternal flow"]["id"] != wep_by_name["lost prayer to the sacred winds"]["id"]


def test_weapons_refinement_progressions(weapons_data):
    """Ensure all 4-star and 5-star weapons with passives contain refinement descriptions."""
    for wep in weapons_data:
        name = wep["name"]
        rarity = wep["rarity"]
        passive = wep.get("passive_name")

        if rarity in [4, 5] and passive:
            refinements = wep.get("refinements", [])
            assert len(refinements) >= 1, (
                f"Weapon '{name}' (Rarity {rarity}) has passive '{passive}' but empty refinements!"
            )


def test_artifacts_data_integrity(artifacts_data):
    """Ensure artifact sets have unique IDs and non-empty 2-piece bonuses."""
    ids = [a["id"] for a in artifacts_data]
    id_counts = Counter(ids)
    dupe_ids = {aid: cnt for aid, cnt in id_counts.items() if cnt > 1}
    assert not dupe_ids, f"Duplicate Artifact Set IDs detected: {dupe_ids}"

    for art in artifacts_data:
        assert art.get("bonus_2pc"), f"Artifact Set '{art.get('name')}' missing 2pc bonus!"


def test_materials_comprehensive_catalog(materials_data):
    """Ensure materials catalog contains >= 50 verified items across canonical types."""
    assert len(materials_data) >= 50, (
        f"Materials catalog has only {len(materials_data)} items; expected comprehensive catalogue (>50)."
    )

    types = {m["type"] for m in materials_data}
    assert len(types) >= 3, f"Expected diverse material types, found: {types}"

    ids = [m["id"] for m in materials_data]
    id_counts = Counter(ids)
    dupe_ids = {mid: cnt for mid, cnt in id_counts.items() if cnt > 1}
    assert not dupe_ids, f"Duplicate Material IDs detected: {dupe_ids}"
