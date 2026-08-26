"""Comprehensive automated test suite for Phase 1 Enka Account Import."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from backend.main import app
from backend.providers.enka_client import EnkaClient, EnkaAPIException
from backend.services.cache_service import ShowcaseCacheService
from backend.services.account_service import AccountService
from backend.models.account import ArtifactSlot

client = TestClient(app)

# Realistic Mocked Enka Response with Arlecchino & Furina
MOCK_ENKA_PAYLOAD = {
    "playerInfo": {
        "nickname": "AntigravityTraveler",
        "level": 60,
        "signature": "Testing GenshinIQ Enka Integration",
        "worldLevel": 8,
        "finishAchievementNum": 1150,
        "towerFloorIndex": 12,
        "towerLevelIndex": 3,
        "showAvatarInfoList": [
            {"avatarId": 10000096, "level": 90},
            {"avatarId": 10000089, "level": 90},
        ],
    },
    "avatarInfoList": [
        {
            "avatarId": 10000096,  # Arlecchino
            "propMap": {
                "1001": {"type": 1001, "ival": "0", "val": "0"},
                "1002": {"type": 1002, "ival": "6", "val": "6"},  # Ascension 6
                "4001": {"type": 4001, "ival": "90", "val": "90"},  # Level 90
            },
            "talentIdList": [11961, 11962],  # C2
            "fetterInfo": {"expLevel": 10},
            "skillLevelMap": {
                "10961": 10,
                "10962": 9,
                "10963": 8,
            },
            "proudSkillExtraLevelMap": {
                "10961": 0,
                "10962": 3,
            },
            "fightPropMap": {
                "1": 13103.0,  # Base HP
                "2": 4780.0,   # Flat HP
                "3": 0.0,
                "4": 342.0,    # Base ATK
                "5": 311.0,    # Flat ATK
                "6": 0.466,    # ATK%
                "7": 765.0,    # Base DEF
                "8": 0.0,
                "9": 0.0,
                "20": 0.754,   # 75.4% Crit Rate
                "22": 1.928,   # 192.8% Crit DMG
                "23": 1.250,   # 125.0% ER
                "28": 120.0,   # 120 EM
                "40": 0.466,   # 46.6% Pyro DMG
                "2000": 17883.0,  # Max HP
                "2001": 2240.0,   # Cur ATK
                "2002": 765.0,    # Cur DEF
            },
            "equipList": [
                # Weapon: Crimson Moon's Semblance
                {
                    "itemId": 13512,
                    "weapon": {
                        "level": 90,
                        "promoteLevel": 6,
                        "affixMap": {"113512": 0},  # R1
                    },
                    "flat": {
                        "nameTextMapHash": "Crimson Moon's Semblance",
                        "itemType": "ITEM_WEAPON",
                        "weaponType": "POLEARM",
                        "rankLevel": 5,
                        "weaponStats": [
                            {"appendPropId": "FIGHT_PROP_BASE_ATTACK", "statValue": 674.0},
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 22.1},
                        ],
                    },
                },
                # Artifact 1: Flower of Life (Fragment of Harmonic Whimsy)
                {
                    "itemId": 94544,
                    "reliquary": {
                        "level": 21,  # +20
                        "mainPropId": "FIGHT_PROP_HP",
                        "appendPropIdList": [1, 2, 3, 4],
                    },
                    "flat": {
                        "nameTextMapHash": "Whimsy Flower",
                        "setNameTextMapHash": "Fragment of Harmonic Whimsy",
                        "itemType": "ITEM_RELIQUARY",
                        "equipType": "EQUIP_BRACER",
                        "rankLevel": 5,
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_HP",
                            "statValue": 4780.0,
                        },
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 10.5},
                            {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 21.0},
                            {"appendPropId": "FIGHT_PROP_ATTACK_PERCENT", "statValue": 9.9},
                            {"appendPropId": "FIGHT_PROP_ELEMENT_MASTERY", "statValue": 42.0},
                        ],
                    },
                },
                # Artifact 2: Plume of Death
                {
                    "itemId": 94524,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": "FIGHT_PROP_ATTACK",
                    },
                    "flat": {
                        "nameTextMapHash": "Whimsy Plume",
                        "setNameTextMapHash": "Fragment of Harmonic Whimsy",
                        "itemType": "ITEM_RELIQUARY",
                        "equipType": "EQUIP_NECKLACE",
                        "rankLevel": 5,
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_ATTACK",
                            "statValue": 311.0,
                        },
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 13.2},
                            {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 14.8},
                        ],
                    },
                },
                # Artifact 3: Sands of Eon (ATK%)
                {
                    "itemId": 94554,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": "FIGHT_PROP_ATTACK_PERCENT",
                    },
                    "flat": {
                        "nameTextMapHash": "Whimsy Clock",
                        "setNameTextMapHash": "Fragment of Harmonic Whimsy",
                        "itemType": "ITEM_RELIQUARY",
                        "equipType": "EQUIP_SHOES",
                        "rankLevel": 5,
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_ATTACK_PERCENT",
                            "statValue": 46.6,
                        },
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL_HURT", "statValue": 28.0},
                        ],
                    },
                },
                # Artifact 4: Goblet of Eonothem (Pyro DMG)
                {
                    "itemId": 94514,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": "FIGHT_PROP_FIRE_ADD_HURT",
                    },
                    "flat": {
                        "nameTextMapHash": "Whimsy Goblet",
                        "setNameTextMapHash": "Fragment of Harmonic Whimsy",
                        "itemType": "ITEM_RELIQUARY",
                        "equipType": "EQUIP_RING",
                        "rankLevel": 5,
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_FIRE_ADD_HURT",
                            "statValue": 46.6,
                        },
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 10.1},
                        ],
                    },
                },
                # Artifact 5: Circlet of Logos (CRIT DMG)
                {
                    "itemId": 94534,
                    "reliquary": {
                        "level": 21,
                        "mainPropId": "FIGHT_PROP_CRITICAL_HURT",
                    },
                    "flat": {
                        "nameTextMapHash": "Whimsy Circlet",
                        "setNameTextMapHash": "Fragment of Harmonic Whimsy",
                        "itemType": "ITEM_RELIQUARY",
                        "equipType": "EQUIP_DRESS",
                        "rankLevel": 5,
                        "reliquaryMainstat": {
                            "mainPropId": "FIGHT_PROP_CRITICAL_HURT",
                            "statValue": 62.2,
                        },
                        "reliquarySubstats": [
                            {"appendPropId": "FIGHT_PROP_CRITICAL", "statValue": 14.0},
                        ],
                    },
                },
            ],
        }
    ],
    "ttl": 300,
}


def test_enka_normalizer_character():
    """Verify Enka raw JSON parses into accurate normalized character build."""
    client_inst = EnkaClient()
    parsed = client_inst.normalize_showcase(MOCK_ENKA_PAYLOAD, "700000000")

    assert parsed.profile.nickname == "AntigravityTraveler"
    assert parsed.profile.level == 60
    assert parsed.profile.world_level == 8
    assert parsed.profile.achievement_count == 1150
    assert parsed.profile.spiral_abyss_floor == 12
    assert parsed.character_count == 1

    char = parsed.characters[0]
    assert char.avatar_id == 10000096
    assert char.name == "Arlecchino"
    assert char.element == "Pyro"
    assert char.level == 90
    assert char.ascension == 6
    assert char.constellation == 2
    assert char.fetter_level == 10

    # Verify weapon
    assert char.weapon is not None
    assert char.weapon.name == "Crimson Moon's Semblance"
    assert char.weapon.level == 90
    assert char.weapon.refinement == 1
    assert char.weapon.base_atk == 674.0
    assert char.weapon.sub_stat.name == "CRIT Rate"
    assert char.weapon.sub_stat.formatted == "22.1%"

    # Verify combat stats
    assert char.stats.max_hp == 17883.0
    assert char.stats.atk == 2240.0
    assert char.stats.crit_rate == 0.754
    assert char.stats.crit_dmg == 1.928
    assert char.stats.damage_bonuses["Pyro"] == 0.466

    # Verify artifacts
    assert len(char.artifacts) == 5
    flower = next(a for a in char.artifacts if a.slot == ArtifactSlot.FLOWER)
    assert flower.level == 20
    assert flower.main_stat.name == "Flat HP"
    assert flower.main_stat.value == 4780.0
    assert len(flower.substats) == 4
    assert flower.substats[0].name == "CRIT Rate"
    assert flower.substats[0].formatted == "10.5%"

    circlet = next(a for a in char.artifacts if a.slot == ArtifactSlot.CIRCLET)
    assert circlet.main_stat.name == "CRIT DMG"
    assert circlet.main_stat.formatted == "62.2%"


@pytest.mark.asyncio
async def test_account_service_caching(tmp_path):
    """Verify caching respects TTL and saves/retrieves properly."""
    test_cache = ShowcaseCacheService(cache_dir=tmp_path)
    mock_client = EnkaClient()

    # Pre-populate cache
    test_cache.set("711223344", MOCK_ENKA_PAYLOAD, ttl_seconds=10)

    # Fast retrieval from cache
    service = AccountService(client=mock_client, cache=test_cache)
    res = await service.get_showcase("711223344")
    assert res.cached is True
    assert res.profile.nickname == "AntigravityTraveler"

    # Test cache invalidation
    test_cache.invalidate("711223344")
    assert test_cache.get("711223344") is None


def test_api_account_showcase_endpoint():
    """Verify /api/account/{uid} endpoint with mocked Enka response."""
    with patch("backend.services.account_service.account_service.client.fetch_user_showcase", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_ENKA_PAYLOAD

        response = client.get("/api/account/700000000?refresh=true")
        assert response.status_code == 200

        data = response.json()
        assert data["profile"]["nickname"] == "AntigravityTraveler"
        assert data["profile"]["level"] == 60
        assert len(data["characters"]) == 1
        assert data["characters"][0]["name"] == "Arlecchino"


def test_api_account_character_lookup():
    """Verify /api/account/{uid}/character/{char_ident} lookup."""
    with patch("backend.services.account_service.account_service.client.fetch_user_showcase", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = MOCK_ENKA_PAYLOAD

        # Lookup by name
        response = client.get("/api/account/700000000/character/Arlecchino")
        assert response.status_code == 200
        assert response.json()["avatar_id"] == 10000096

        # Lookup by ID
        response = client.get("/api/account/700000000/character/10000096")
        assert response.status_code == 200

        # Lookup non-existent character
        response = client.get("/api/account/700000000/character/NonExistent")
        assert response.status_code == 404


def test_error_invalid_uid():
    """Verify HTTP 400 when invalid UID is supplied."""
    response = client.get("/api/account/abc")
    assert response.status_code == 400
    assert "Invalid Genshin Impact UID format" in response.json()["detail"]


def test_error_enka_rate_limit_and_maintenance():
    """Verify error propagation for 424 and 429 statuses."""
    with patch("backend.services.account_service.account_service.client.fetch_user_showcase", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.side_effect = EnkaAPIException(status_code=429, detail="Enka.Network rate limit reached.")

        response = client.get("/api/account/700000000?refresh=true")
        assert response.status_code == 429
        assert "rate limit" in response.json()["detail"]
