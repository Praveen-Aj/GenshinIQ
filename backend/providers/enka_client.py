"""Enka.Network API Client and Raw Data Normalizer."""

import httpx
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
from fastapi import HTTPException

from backend.config import settings
from backend.models.account import (
    EnkaShowcaseResponse,
    PlayerProfile,
    CharacterBuild,
    CombatStats,
    WeaponData,
    ArtifactData,
    ArtifactSlot,
    StatValue,
    Substat,
    TalentData,
)
from backend.services.enka_mappings import (
    EQUIP_SLOT_MAP,
    FIGHT_PROP_INFO,
    NUMERIC_FIGHT_PROP_MAP,
    get_character_info,
    format_stat_value,
    resolve_weapon_name,
    resolve_artifact_set_name,
)

USER_AGENT = "GenshinIQ/0.1.0 (https://github.com/genshiniq; contact@genshiniq.local)"


class EnkaAPIException(HTTPException):
    """Custom exception wrapper for Enka API errors."""
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)


class EnkaClient:
    """Asynchronous client for interacting with Enka.Network API."""

    def __init__(self, base_url: Optional[str] = None):
        self.base_url = (base_url or settings.ENKA_API_BASE_URL).rstrip("/")
        self.headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
        }

    async def fetch_user_showcase(self, uid: str) -> Dict[str, Any]:
        """
        Fetch raw showcase data from Enka.Network for a given UID.
        Raises EnkaAPIException on failure.
        """
        clean_uid = str(uid).strip()
        if not clean_uid.isdigit() or len(clean_uid) not in [9, 10]:
            raise EnkaAPIException(
                status_code=400,
                detail=f"Invalid Genshin Impact UID format: '{uid}'. Expected 9 or 10 numeric digits."
            )

        url = f"{self.base_url}/uid/{clean_uid}"

        try:
            async with httpx.AsyncClient(timeout=12.0, headers=self.headers) as client:
                response = await client.get(url)

                if response.status_code == 200:
                    try:
                        return response.json()
                    except Exception as e:
                        raise EnkaAPIException(
                            status_code=502,
                            detail=f"Enka returned invalid JSON payload: {str(e)}"
                        )

                elif response.status_code == 400:
                    raise EnkaAPIException(status_code=400, detail="Invalid UID format requested by Enka API.")
                elif response.status_code == 404:
                    raise EnkaAPIException(status_code=404, detail=f"Player UID {clean_uid} not found on Enka.Network.")
                elif response.status_code == 424:
                    raise EnkaAPIException(status_code=424, detail="Enka.Network is currently updating or in game maintenance.")
                elif response.status_code == 429:
                    retry_after = response.headers.get("Retry-After", "60")
                    raise EnkaAPIException(
                        status_code=429,
                        detail=f"Enka.Network rate limit reached. Please wait {retry_after}s before retrying."
                    )
                elif response.status_code in [500, 502, 503, 504]:
                    raise EnkaAPIException(
                        status_code=503,
                        detail="Enka.Network service is currently unavailable. Please try again later."
                    )
                else:
                    raise EnkaAPIException(
                        status_code=response.status_code,
                        detail=f"Enka API returned unexpected status {response.status_code}: {response.text}"
                    )

        except httpx.RequestError as exc:
            raise EnkaAPIException(
                status_code=503,
                detail=f"Network error connecting to Enka.Network: {str(exc)}"
            )

    def normalize_showcase(self, raw_data: Dict[str, Any], uid: str, cached: bool = False) -> EnkaShowcaseResponse:
        """
        Transform raw Enka JSON payload into normalized Pydantic models.
        """
        player_info = raw_data.get("playerInfo", {})
        avatar_info_list = raw_data.get("avatarInfoList", [])
        ttl = raw_data.get("ttl", settings.ENKA_CACHE_TTL_SECONDS)

        # 1. Parse Player Profile
        profile = PlayerProfile(
            uid=str(uid),
            nickname=player_info.get("nickname", "Traveler"),
            level=player_info.get("level", 1),
            world_level=player_info.get("worldLevel", 0),
            signature=player_info.get("signature"),
            achievement_count=player_info.get("finishAchievementNum", 0),
            spiral_abyss_floor=player_info.get("towerFloorIndex"),
            spiral_abyss_chamber=player_info.get("towerLevelIndex"),
            name_card_id=player_info.get("nameCardId"),
            showcase_character_ids=[
                item.get("avatarId")
                for item in player_info.get("showAvatarInfoList", [])
                if "avatarId" in item
            ],
        )

        # 2. Parse Characters in showcase
        characters: List[CharacterBuild] = []
        for avatar in avatar_info_list:
            char_build = self._parse_character(avatar)
            if char_build:
                characters.append(char_build)

        return EnkaShowcaseResponse(
            profile=profile,
            characters=characters,
            character_count=len(characters),
            ttl=ttl,
            cached=cached,
            fetched_at=datetime.now(timezone.utc).isoformat(),
        )

    def _parse_character(self, avatar: Dict[str, Any]) -> Optional[CharacterBuild]:
        """Parse an individual character build object from avatarInfoList."""
        avatar_id = avatar.get("avatarId")
        if not avatar_id:
            return None

        name, element, rarity = get_character_info(avatar_id)
        prop_map = avatar.get("propMap", {})

        # Level & Ascension
        level = int(prop_map.get("4001", {}).get("val", 1))
        ascension = int(prop_map.get("1002", {}).get("val", 0))

        # Constellations (count of unlocked talentIdList)
        talent_id_list = avatar.get("talentIdList", [])
        constellation = len(talent_id_list)

        # Friendship level
        fetter_info = avatar.get("fetterInfo", {})
        fetter_level = int(fetter_info.get("expLevel", 10))

        # Combat Stats
        fight_prop_map = avatar.get("fightPropMap", {})
        stats, raw_stats = self._parse_combat_stats(fight_prop_map)

        # Talents
        talents = self._parse_talents(avatar)

        # Equip List (Weapon & Artifacts)
        weapon, artifacts = self._parse_equip_list(avatar.get("equipList", []))

        return CharacterBuild(
            avatar_id=avatar_id,
            name=name,
            element=element,
            rarity=rarity,
            level=level,
            ascension=ascension,
            constellation=constellation,
            fetter_level=fetter_level,
            costume_id=avatar.get("costumeId"),
            talents=talents,
            weapon=weapon,
            artifacts=artifacts,
            stats=stats,
            raw_fight_prop_map=raw_stats,
        )

    def _parse_combat_stats(self, fight_prop_map: Dict[Any, Any]) -> Tuple[CombatStats, Dict[str, float]]:
        """Parse raw fightPropMap into normalized CombatStats."""
        raw_stats: Dict[str, float] = {}

        for k, v in fight_prop_map.items():
            key_str = NUMERIC_FIGHT_PROP_MAP.get(int(k), str(k)) if str(k).isdigit() else str(k)
            raw_stats[key_str] = float(v)

        def get_stat(key: str, default: float = 0.0) -> float:
            return raw_stats.get(key, default)

        base_hp = get_stat("FIGHT_PROP_BASE_HP")
        cur_hp = get_stat("FIGHT_PROP_MAX_HP") or (base_hp * (1.0 + get_stat("FIGHT_PROP_HP_PERCENT")) + get_stat("FIGHT_PROP_HP"))

        base_atk = get_stat("FIGHT_PROP_BASE_ATTACK")
        cur_atk = get_stat("FIGHT_PROP_CUR_ATTACK") or (base_atk * (1.0 + get_stat("FIGHT_PROP_ATTACK_PERCENT")) + get_stat("FIGHT_PROP_ATTACK"))

        base_def = get_stat("FIGHT_PROP_BASE_DEFENSE")
        cur_def = get_stat("FIGHT_PROP_CUR_DEFENSE") or (base_def * (1.0 + get_stat("FIGHT_PROP_DEFENSE_PERCENT")) + get_stat("FIGHT_PROP_DEFENSE"))

        dmg_bonuses = {
            "Pyro": get_stat("FIGHT_PROP_FIRE_ADD_HURT"),
            "Hydro": get_stat("FIGHT_PROP_WATER_ADD_HURT"),
            "Cryo": get_stat("FIGHT_PROP_ICE_ADD_HURT"),
            "Electro": get_stat("FIGHT_PROP_ELEC_ADD_HURT"),
            "Anemo": get_stat("FIGHT_PROP_WIND_ADD_HURT"),
            "Geo": get_stat("FIGHT_PROP_ROCK_ADD_HURT"),
            "Dendro": get_stat("FIGHT_PROP_GRASS_ADD_HURT"),
            "Physical": get_stat("FIGHT_PROP_PHYSICAL_ADD_HURT"),
        }

        combat_stats = CombatStats(
            max_hp=round(cur_hp, 1),
            base_hp=round(base_hp, 1),
            atk=round(cur_atk, 1),
            base_atk=round(base_atk, 1),
            defense=round(cur_def, 1),
            base_def=round(base_def, 1),
            crit_rate=round(get_stat("FIGHT_PROP_CRITICAL", 0.05), 4),
            crit_dmg=round(get_stat("FIGHT_PROP_CRITICAL_HURT", 0.50), 4),
            energy_recharge=round(get_stat("FIGHT_PROP_CHARGE_EFFICIENCY", 1.00), 4),
            elemental_mastery=round(get_stat("FIGHT_PROP_ELEMENT_MASTERY", 0.0), 1),
            healing_bonus=round(get_stat("FIGHT_PROP_HEAL_ADD", 0.0), 4),
            shield_strength=round(get_stat("FIGHT_PROP_SHIELD_COST_MINUS_RATIO", 0.0), 4),
            damage_bonuses=dmg_bonuses,
        )

        return combat_stats, raw_stats

    def _parse_talents(self, avatar: Dict[str, Any]) -> List[TalentData]:
        """Parse skillLevelMap and proudSkillExtraLevelMap."""
        skill_level_map = avatar.get("skillLevelMap", {})
        proud_skill_map = avatar.get("proudSkillExtraLevelMap", {})

        talents: List[TalentData] = []
        for skill_id_str, base_lvl in skill_level_map.items():
            skill_id = int(skill_id_str)
            extra_lvl = proud_skill_map.get(skill_id_str, 0)
            boosted_lvl = base_lvl + extra_lvl

            talents.append(
                TalentData(
                    skill_id=skill_id,
                    name=f"Talent_{skill_id}",
                    level=int(base_lvl),
                    boosted_level=int(boosted_lvl),
                )
            )
        return talents

    def _parse_equip_list(self, equip_list: List[Dict[str, Any]]) -> Tuple[Optional[WeaponData], List[ArtifactData]]:
        """Parse equipment list into Weapon and Artifact objects."""
        weapon: Optional[WeaponData] = None
        artifacts: List[ArtifactData] = []

        for equip in equip_list:
            flat = equip.get("flat", {})
            item_type = flat.get("itemType")

            if item_type == "ITEM_WEAPON" or "weapon" in equip:
                weapon = self._parse_weapon(equip)
            elif item_type == "ITEM_RELIQUARY" or "reliquary" in equip:
                art = self._parse_artifact(equip)
                if art:
                    artifacts.append(art)

        return weapon, artifacts

    def _parse_weapon(self, equip: Dict[str, Any]) -> WeaponData:
        """Parse weapon data."""
        item_id = equip.get("itemId", 0)
        weapon_info = equip.get("weapon", {})
        flat = equip.get("flat", {})

        level = weapon_info.get("level", 1)
        ascension = weapon_info.get("promoteLevel", 0)

        affix_map = weapon_info.get("affixMap", {})
        refinement = 1
        if affix_map:
            refinement = list(affix_map.values())[0] + 1

        fallback_name = flat.get("nameTextMapHash", f"Weapon_{item_id}")
        icon_str = flat.get("icon")
        canonical_name, weapon_type, rarity = resolve_weapon_name(item_id, fallback_name, icon_str)

        base_atk = None
        sub_stat = None
        for stat_obj in flat.get("weaponStats", []):
            prop_type = stat_obj.get("appendPropId", "")
            stat_value = float(stat_obj.get("statValue", 0.0))
            if "BASE_ATTACK" in prop_type:
                base_atk = stat_value
            else:
                s_name, s_formatted, is_pct = format_stat_value(prop_type, stat_value)
                sub_stat = StatValue(
                    key=prop_type,
                    name=s_name,
                    value=stat_value,
                    formatted=s_formatted,
                    is_percent=is_pct,
                )

        return WeaponData(
            item_id=item_id,
            name=canonical_name,
            weapon_type=weapon_type,
            rarity=rarity,
            level=level,
            ascension=ascension,
            refinement=refinement,
            icon=icon_str,
            base_atk=base_atk,
            sub_stat=sub_stat,
        )

    def _parse_artifact(self, equip: Dict[str, Any]) -> Optional[ArtifactData]:
        """Parse artifact data."""
        item_id = equip.get("itemId", 0)
        reliquary = equip.get("reliquary", {})
        flat = equip.get("flat", {})

        equip_type = flat.get("equipType", "")
        slot = EQUIP_SLOT_MAP.get(equip_type, ArtifactSlot.FLOWER)

        rarity = flat.get("rankLevel", 5)
        level_raw = reliquary.get("level", 1)
        level = max(0, level_raw - 1)

        # Main stat
        main_stat_obj = flat.get("reliquaryMainstat", {})
        main_prop_id = main_stat_obj.get("mainPropId", "FIGHT_PROP_HP")
        main_stat_val = float(main_stat_obj.get("statValue", 0.0))
        m_name, m_formatted, m_is_pct = format_stat_value(main_prop_id, main_stat_val)

        main_stat = StatValue(
            key=main_prop_id,
            name=m_name,
            value=main_stat_val,
            formatted=m_formatted,
            is_percent=m_is_pct,
        )

        # Substats
        substats: List[Substat] = []
        for sub_obj in flat.get("reliquarySubstats", []):
            append_prop_id = sub_obj.get("appendPropId", "")
            stat_value = float(sub_obj.get("statValue", 0.0))
            s_name, s_formatted, s_is_pct = format_stat_value(append_prop_id, stat_value)
            substats.append(
                Substat(
                    key=append_prop_id,
                    name=s_name,
                    value=stat_value,
                    formatted=s_formatted,
                    is_percent=s_is_pct,
                )
            )

        name = flat.get("nameTextMapHash", f"Artifact_{item_id}")
        set_hash = flat.get("setNameTextMapHash", "Artifact Set")
        icon_str = flat.get("icon")
        set_name = resolve_artifact_set_name(set_hash, name, icon_str)

        return ArtifactData(
            item_id=item_id,
            name=name,
            slot=slot,
            set_name=set_name,
            icon=icon_str,
            rarity=rarity,
            level=level,
            main_stat=main_stat,
            substats=substats,
        )


enka_client = EnkaClient()
