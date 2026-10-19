import pytest
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_guides_summary_endpoint():
    res = client.get("/api/guides/summary")
    assert res.status_code == 200
    data = res.json()
    assert "total_guides" in data
    assert data["total_guides"] > 100
    assert "curated_guides" in data
    assert "archetype_baselines" in data
    assert "categories" in data
    cats = data["categories"]
    assert "characters" in cats
    assert "weapons" in cats
    assert "artifacts" in cats
    assert "teams" in cats
    assert "mechanics" in cats
    assert "farming" in cats

def test_guides_list_filtering():
    # Category = characters
    res = client.get("/api/guides?category=characters")
    assert res.status_code == 200
    data = res.json()
    items = data if isinstance(data, list) else data["items"]
    assert len(items) > 50
    for item in items:
        assert item["category"] == "characters"
        assert "id" in item
        assert "title" in item
        assert "guide_type" in item

    # Category = weapons
    res_wep = client.get("/api/guides?category=weapons")
    assert res_wep.status_code == 200
    data_wep = res_wep.json()
    items_wep = data_wep if isinstance(data_wep, list) else data_wep["items"]
    assert len(items_wep) > 50
    for item in items_wep:
        assert item["category"] == "weapons"
        assert "weapon_type" in item

    # Filter by element
    res_pyro = client.get("/api/guides?category=characters&element=Pyro")
    assert res_pyro.status_code == 200
    data_pyro = res_pyro.json()
    items_pyro = data_pyro if isinstance(data_pyro, list) else data_pyro["items"]
    assert len(items_pyro) > 0
    for item in items_pyro:
        assert item["element"].lower() == "pyro"

    # Search query
    res_q = client.get("/api/guides?q=Arlecchino")
    assert res_q.status_code == 200
    data_q = res_q.json()
    items_q = data_q if isinstance(data_q, list) else data_q["items"]
    assert any(i["title"] == "Arlecchino" for i in items_q)

def test_character_guide_detail():
    res = client.get("/api/guides/character/Arlecchino")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Arlecchino"
    assert data["element"] == "Pyro"
    assert data["weapon_type"] == "Polearm"
    assert "weapon_recommendations" in data
    assert len(data["weapon_recommendations"]) > 0
    assert "artifact_recommendations" in data
    assert len(data["artifact_recommendations"]) > 0
    assert "talent_priority" in data
    assert "stat_targets" in data
    assert "teams" in data
    assert "ai_actions" in data
    assert len(data["ai_actions"]) >= 2
    # Verify AI actions have runnable prompts
    for action in data["ai_actions"]:
        assert "label" in action
        assert "prompt" in action
        assert len(action["prompt"]) > 10

def test_character_guide_nonexistent():
    res = client.get("/api/guides/character/NonexistentCharacter12345")
    assert res.status_code == 404

def test_weapon_guide_detail_and_scaling():
    res = client.get("/api/guides/weapon/Crimson Moon's Semblance")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Crimson Moon's Semblance"
    assert data["weapon_type"] == "Polearm"
    assert data["rarity"] == 5
    assert data["base_atk_lv1"] > 0
    assert data["base_atk_lv90"] > data["base_atk_lv1"]
    assert "refinement_scaling" in data
    assert "notable_users" in data
    assert "ai_actions" in data

def test_weapon_guide_nonexistent():
    res = client.get("/api/guides/weapon/FakePlasticSword999")
    assert res.status_code == 404

def test_artifact_guide_detail():
    res = client.get("/api/guides/artifact/Fragment of Harmonic Whimsy")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Fragment of Harmonic Whimsy"
    assert "bonus_2pc" in data
    assert "bonus_4pc" in data
    assert "notable_users" in data
    assert "domain_info" in data
    assert "ai_actions" in data

def test_artifact_guide_nonexistent():
    res = client.get("/api/guides/artifact/UnknownRelicSet999")
    assert res.status_code == 404

def test_mechanics_guide_detail():
    res = client.get("/api/guides/mechanics/elemental_reactions")
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "visual_sections" in data
    assert len(data["visual_sections"]) > 0
    assert "key_formulas" in data
    assert "ai_actions" in data

def test_mechanics_guide_nonexistent():
    res = client.get("/api/guides/mechanics/quantum_gravity_time_travel")
    assert res.status_code == 404

def test_teams_guide_detail():
    res = client.get("/api/guides/teams/national")
    assert res.status_code == 200
    data = res.json()
    assert "title" in data
    assert "core_characters" in data
    assert len(data["core_characters"]) == 4
    assert "rotation_steps" in data
    assert len(data["rotation_steps"]) > 0
    assert "variants" in data

def test_farming_guide_detail():
    res = client.get("/api/guides/farming")
    assert res.status_code == 200
    data = res.json()
    assert "regions" in data
    regions = data["regions"]
    for reg in ["mondstadt", "liyue", "inazuma", "sumeru", "fontaine", "natlan"]:
        assert reg in regions

def test_guide_sanitization_no_internal_source_leak():
    """Ensure no raw internal source IDs (src_*) or scraper names leak in guide responses."""
    endpoints = [
        "/api/guides/summary",
        "/api/guides?category=characters",
        "/api/guides/character/Arlecchino",
        "/api/guides/weapon/Crimson Moon's Semblance",
        "/api/guides/artifact/Fragment of Harmonic Whimsy",
        "/api/guides/teams/national",
        "/api/guides/mechanics/elemental_reactions",
        "/api/guides/farming",
    ]
    for ep in endpoints:
        res = client.get(ep)
        assert res.status_code == 200
        text = res.text
        assert "src_" not in text, f"Found internal source ID leak in {ep}"
        assert "Honey Hunter" not in text, f"Found scraper name in {ep}"


def test_dynamic_curated_characters_discovery():
    """Verify that curated characters are dynamically discovered from knowledge files."""
    from backend.services.encyclopedia_service import encyclopedia_service
    from backend.services.guide_service import guide_service

    curated = encyclopedia_service.get_curated_characters()
    assert len(curated) >= 15
    # Citlali has a KQM guide and must be included
    assert "citlali" in curated
    assert "arlecchino" in curated
    assert "furina" in curated
    assert "neuvillette" in curated
    # Guide service must match encyclopedia service
    assert guide_service._curated_chars == curated


def test_character_guide_deterministic_talents_and_constellations():
    """Verify character guide contains real deterministic talents & constellations from package."""
    res = client.get("/api/guides/character/Kamisato Ayaka")
    assert res.status_code == 200
    data = res.json()
    assert data["name"] == "Kamisato Ayaka"

    # Talents breakdown must contain actual Ayaka skill names
    talents = data.get("talents_breakdown", [])
    assert len(talents) >= 3
    talent_names = [t["name"] for t in talents]
    assert any("Kamisato Art" in n or "Kabuki" in n for n in talent_names)
    assert any("Soumetsu" in n for n in talent_names)

    # Constellations summary must contain actual constellation names
    consts = data.get("constellations_summary", [])
    assert len(consts) >= 4
    const_names = [c["name"] for c in consts]
    assert any("Sakura" in n or "Seki no To" in n for n in const_names)


def test_character_guide_taxonomy_integrity():
    """Ensure accurate distinction between Curated Theorycrafting and Reference/Baseline."""
    # Curated character (e.g. Arlecchino)
    res_curated = client.get("/api/guides/character/Arlecchino")
    assert res_curated.status_code == 200
    data_curated = res_curated.json()
    assert data_curated["guide_type"] == "CURATED_CHARACTER_GUIDE"
    assert "Curated Theorycrafting" in data_curated["guide_badge"]

    # Canonical reference character (e.g. Kamisato Ayaka)
    res_ref = client.get("/api/guides/character/Kamisato Ayaka")
    assert res_ref.status_code == 200
    data_ref = res_ref.json()
    assert data_ref["guide_type"] == "GENERIC_FALLBACK"
    assert "Archetype Baseline" in data_ref["guide_badge"]
    assert "Canonical game reference" in data_ref["provenance_note"]

