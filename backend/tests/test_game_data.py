"""Automated tests for Phase 2 Structured Genshin Data."""

import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.services.game_data_service import game_data_service

client = TestClient(app)


def test_character_service_lookups():
    """Verify character lookup by ID and case-insensitive name."""
    # Lookup by name
    arlecchino = game_data_service.get_character("Arlecchino")
    assert arlecchino is not None
    assert arlecchino.id == 10000096
    assert arlecchino.element == "Pyro"
    assert arlecchino.weapon_type == "Polearm"
    assert arlecchino.rarity == 5
    assert arlecchino.base_atk_lvl90 == 342.0
    assert arlecchino.ascension_stat == "CRIT DMG"
    assert len(arlecchino.talents) >= 3
    assert len(arlecchino.constellations) == 6
    assert "Fragment of a Golden Melody" in arlecchino.ascension_materials

    # Case-insensitive lookup
    furina = game_data_service.get_character("furina")
    assert furina is not None
    assert furina.element == "Hydro"
    assert furina.rarity == 5

    # Lookup by ID
    neuvi = game_data_service.get_character("10000087")
    assert neuvi is not None
    assert neuvi.name == "Neuvillette"
    assert neuvi.element == "Hydro"


def test_character_filtering():
    """Verify character filtering by element and rarity."""
    pyro_chars = game_data_service.list_characters(element="Pyro")
    assert len(pyro_chars) >= 3
    for c in pyro_chars:
        assert c.element == "Pyro"

    four_stars = game_data_service.list_characters(rarity=4)
    assert len(four_stars) >= 3
    for c in four_stars:
        assert c.rarity == 4


def test_weapon_service_lookups():
    """Verify weapon lookup, stats, and refinements."""
    cms = game_data_service.get_weapon("Crimson Moon's Semblance")
    assert cms is not None
    assert cms.id == 13512
    assert cms.weapon_type == "Polearm"
    assert cms.rarity == 5
    assert cms.base_atk_lvl90 == 674.0
    assert cms.sub_stat_type == "CRIT Rate"
    assert cms.sub_stat_val_lvl90 == "22.1%"
    assert len(cms.refinements) == 5

    # Lookup by ID
    sword = game_data_service.get_weapon("11513")
    assert sword is not None
    assert sword.name == "Splendor of Tranquil Waters"


def test_artifact_service_lookups():
    """Verify artifact set 2pc & 4pc bonus text."""
    whimsy = game_data_service.get_artifact_set("Fragment of Harmonic Whimsy")
    assert whimsy is not None
    assert whimsy.id == 15035
    assert "18%" in whimsy.bonus_2pc
    assert "Bond of Life" in whimsy.bonus_4pc
    assert "flower" in whimsy.pieces
    assert whimsy.pieces["circlet"] == "Whimsical Dance of the Withered"


def test_materials_lookups():
    """Verify material list and filtering."""
    materials = game_data_service.list_materials(material_type="Boss Material")
    assert len(materials) >= 1
    assert any("Fragment of a Golden Melody" in m.name for m in materials)


def test_global_search():
    """Verify cross-category unified search."""
    hits = game_data_service.search("Arlecchino")
    assert len(hits) >= 1
    assert hits[0].category == "character"
    assert hits[0].name == "Arlecchino"

    wep_hits = game_data_service.search("Semblance")
    assert len(wep_hits) >= 1
    assert wep_hits[0].category == "weapon"


def test_api_character_endpoints():
    """Verify FastAPI routes for characters and weapons."""
    resp = client.get("/api/data/characters?element=Pyro")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3

    resp_char = client.get("/api/data/characters/Arlecchino")
    assert resp_char.status_code == 200
    assert resp_char.json()["name"] == "Arlecchino"

    resp_wep = client.get("/api/data/weapons/13512")
    assert resp_wep.status_code == 200
    assert resp_wep.json()["name"] == "Crimson Moon's Semblance"

    resp_art = client.get("/api/data/artifacts/15035")
    assert resp_art.status_code == 200
    assert "Whimsy" in resp_art.json()["name"]

    # Not found handling
    resp_404 = client.get("/api/data/characters/UnknownCharacterXYZ")
    assert resp_404.status_code == 404
