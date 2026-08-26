"""Canonical mapping tables for Genshin Impact stats, slots, characters, weapons, and artifacts."""

from typing import Dict, Tuple, Optional, Any
from backend.models.account import ArtifactSlot

# Equip type mapping to internal slot enum
EQUIP_SLOT_MAP: Dict[str, ArtifactSlot] = {
    "EQUIP_BRACER": ArtifactSlot.FLOWER,
    "EQUIP_NECKLACE": ArtifactSlot.PLUME,
    "EQUIP_SHOES": ArtifactSlot.SANDS,
    "EQUIP_RING": ArtifactSlot.GOBLET,
    "EQUIP_DRESS": ArtifactSlot.CIRCLET,
}

# Stat identifier mapping: (Human Name, is_percentage)
FIGHT_PROP_INFO: Dict[str, Tuple[str, bool]] = {
    "FIGHT_PROP_BASE_HP": ("Base HP", False),
    "FIGHT_PROP_HP": ("Flat HP", False),
    "FIGHT_PROP_HP_PERCENT": ("HP%", True),
    "FIGHT_PROP_BASE_ATTACK": ("Base ATK", False),
    "FIGHT_PROP_ATTACK": ("Flat ATK", False),
    "FIGHT_PROP_ATTACK_PERCENT": ("ATK%", True),
    "FIGHT_PROP_BASE_DEFENSE": ("Base DEF", False),
    "FIGHT_PROP_DEFENSE": ("Flat DEF", False),
    "FIGHT_PROP_DEFENSE_PERCENT": ("DEF%", True),
    "FIGHT_PROP_CRITICAL": ("CRIT Rate", True),
    "FIGHT_PROP_CRITICAL_HURT": ("CRIT DMG", True),
    "FIGHT_PROP_CHARGE_EFFICIENCY": ("Energy Recharge", True),
    "FIGHT_PROP_ELEMENT_MASTERY": ("Elemental Mastery", False),
    "FIGHT_PROP_HEAL_ADD": ("Healing Bonus", True),
    "FIGHT_PROP_SHIELD_COST_MINUS_RATIO": ("Shield Strength", True),
    "FIGHT_PROP_PHYSICAL_ADD_HURT": ("Physical DMG Bonus", True),
    "FIGHT_PROP_FIRE_ADD_HURT": ("Pyro DMG Bonus", True),
    "FIGHT_PROP_ELEC_ADD_HURT": ("Electro DMG Bonus", True),
    "FIGHT_PROP_WATER_ADD_HURT": ("Hydro DMG Bonus", True),
    "FIGHT_PROP_WIND_ADD_HURT": ("Anemo DMG Bonus", True),
    "FIGHT_PROP_ICE_ADD_HURT": ("Cryo DMG Bonus", True),
    "FIGHT_PROP_ROCK_ADD_HURT": ("Geo DMG Bonus", True),
    "FIGHT_PROP_GRASS_ADD_HURT": ("Dendro DMG Bonus", True),
}

# Numeric fightPropMap keys commonly found in Enka character objects
NUMERIC_FIGHT_PROP_MAP: Dict[int, str] = {
    1: "FIGHT_PROP_BASE_HP",
    2: "FIGHT_PROP_HP",
    3: "FIGHT_PROP_HP_PERCENT",
    4: "FIGHT_PROP_BASE_ATTACK",
    5: "FIGHT_PROP_ATTACK",
    6: "FIGHT_PROP_ATTACK_PERCENT",
    7: "FIGHT_PROP_BASE_DEFENSE",
    8: "FIGHT_PROP_DEFENSE",
    9: "FIGHT_PROP_DEFENSE_PERCENT",
    20: "FIGHT_PROP_CRITICAL",
    22: "FIGHT_PROP_CRITICAL_HURT",
    23: "FIGHT_PROP_CHARGE_EFFICIENCY",
    26: "FIGHT_PROP_HEAL_ADD",
    28: "FIGHT_PROP_ELEMENT_MASTERY",
    30: "FIGHT_PROP_PHYSICAL_ADD_HURT",
    40: "FIGHT_PROP_FIRE_ADD_HURT",
    41: "FIGHT_PROP_ELEC_ADD_HURT",
    42: "FIGHT_PROP_WATER_ADD_HURT",
    43: "FIGHT_PROP_GRASS_ADD_HURT",
    44: "FIGHT_PROP_WIND_ADD_HURT",
    45: "FIGHT_PROP_ROCK_ADD_HURT",
    46: "FIGHT_PROP_ICE_ADD_HURT",
    2000: "FIGHT_PROP_MAX_HP",
    2001: "FIGHT_PROP_CUR_ATTACK",
    2002: "FIGHT_PROP_CUR_DEFENSE",
}

# Known character mapping: avatarId -> (Name, Element, Rarity)
CHARACTER_DATABASE: Dict[int, Tuple[str, str, int]] = {
    # 5-Star Pyro
    10000096: ("Arlecchino", "Pyro", 5),
    10000060: ("Yelan", "Hydro", 5),
    10000089: ("Furina", "Hydro", 5),
    10000087: ("Neuvillette", "Hydro", 5),
    10000052: ("Raiden Shogun", "Electro", 5),
    10000073: ("Nahida", "Dendro", 5),
    10000047: ("Kaedehara Kazuha", "Anemo", 5),
    10000030: ("Zhongli", "Geo", 5),
    10000046: ("Hu Tao", "Pyro", 5),
    10000002: ("Kamisato Ayaka", "Cryo", 5),
    10000066: ("Kamisato Ayato", "Hydro", 5),
    10000078: ("Alhaitham", "Dendro", 5),
    10000086: ("Wriothesley", "Cryo", 5),
    10000084: ("Lyney", "Pyro", 5),
    10000088: ("Charlotte", "Cryo", 4),
    10000090: ("Chevreuse", "Pyro", 4),
    10000091: ("Navia", "Geo", 5),
    10000092: ("Gaming", "Pyro", 4),
    10000093: ("Xianyun", "Anemo", 5),
    10000094: ("Chiori", "Geo", 5),
    10000095: ("Clorinde", "Electro", 5),
    10000097: ("Sethos", "Electro", 4),
    10000098: ("Sigewinne", "Hydro", 5),
    10000099: ("Emilie", "Dendro", 5),
    10000100: ("Kachina", "Geo", 4),
    10000101: ("Kinich", "Dendro", 5),
    10000102: ("Mualani", "Hydro", 5),
    10000103: ("Xilonen", "Geo", 5),
    10000104: ("Chasca", "Anemo", 5),
    10000106: ("Mavuika", "Pyro", 5),
    10000107: ("Citlali", "Cryo", 5),
    10000108: ("Lan Yan", "Anemo", 4),
    10000114: ("Skirk", "Hydro", 5),
    10000122: ("Nefer", "Dendro", 5),
    10000126: ("Zibai", "Geo", 5),
    # 4-Stars & Classic Staples
    10000032: ("Bennett", "Pyro", 4),
    10000023: ("Xiangling", "Pyro", 4),
    10000015: ("Xingqiu", "Hydro", 4),
    10000034: ("Kujou Sara", "Electro", 4),
    10000036: ("Beidou", "Electro", 4),
    10000031: ("Fischl", "Electro", 4),
    10000043: ("Sucrose", "Anemo", 4),
    10000027: ("Ningguang", "Geo", 4),
    10000064: ("Yun Jin", "Geo", 4),
    10000065: ("Kuki Shinobu", "Electro", 4),
    10000072: ("Candace", "Hydro", 4),
    10000077: ("Faruzan", "Anemo", 4),
    10000079: ("Yaoyao", "Dendro", 4),
    10000083: ("Lynette", "Anemo", 4),
    10000085: ("Freminet", "Cryo", 4),
    10000014: ("Barbara", "Hydro", 4),
    10000025: ("Xiangling", "Pyro", 4),
    10000020: ("Razor", "Electro", 4),
    10000021: ("Amber", "Pyro", 4),
    10000006: ("Lisa", "Electro", 4),
    10000022: ("Venti", "Anemo", 5),
    10000029: ("Klee", "Pyro", 5),
    10000033: ("Tartaglia", "Hydro", 5),
    10000039: ("Noelle", "Geo", 4),
    10000044: ("Diona", "Cryo", 4),
    10000045: ("Rosaria", "Cryo", 4),
    10000048: ("Yanfei", "Pyro", 4),
    10000051: ("Eula", "Cryo", 5),
    10000052: ("Kaedehara Kazuha", "Anemo", 5),
    10000053: ("Sayu", "Anemo", 4),
    10000054: ("Yoimiya", "Pyro", 5),
    10000056: ("Thoma", "Pyro", 4),
    10000057: ("Arataki Itto", "Geo", 5),
    10000058: ("Yae Miko", "Electro", 5),
    10000059: ("Shikanoin Heizou", "Anemo", 4),
    10000060: ("Yelan", "Hydro", 5),
    10000062: ("Collei", "Dendro", 4),
    10000067: ("Dori", "Electro", 4),
    10000068: ("Nilou", "Hydro", 5),
    10000070: ("Cyno", "Electro", 5),
    10000071: ("Wanderer", "Anemo", 5),
    10000073: ("Layla", "Cryo", 4),
    10000074: ("Kaveh", "Dendro", 4),
    10000076: ("Baizhu", "Dendro", 5),
    10000080: ("Kirara", "Dendro", 4),
    10000082: ("Freminet", "Cryo", 4),
    # Cryo Queens & Standard 5-Stars
    10000063: ("Shenhe", "Cryo", 5),
    10000037: ("Ganyu", "Cryo", 5),
    10000038: ("Albedo", "Geo", 5),
    10000003: ("Jean", "Anemo", 5),
    10000016: ("Diluc", "Pyro", 5),
    10000041: ("Mona", "Hydro", 5),
    10000042: ("Keqing", "Electro", 5),
    10000035: ("Qiqi", "Cryo", 5),
    10000069: ("Tighnari", "Dendro", 5),
    10000075: ("Dehya", "Pyro", 5),
    # Travelers
    10000005: ("Aether", "Adaptive", 5),
    10000007: ("Lumine", "Adaptive", 5),
}

# Artifact Set ID / Icon mappings
ARTIFACT_SET_MAP: Dict[int, str] = {
    15041: "Scroll of the Hero of Cinder City",
    15040: "Obsidian Codex",
    15038: "Scroll of the Hero of Cinder City",
    15037: "Obsidian Codex",
    15036: "Unfinished Reverie",
    15035: "Fragment of Harmonic Whimsy",
    15034: "Song of Days Past",
    15033: "Nighttime Whispers in the Echoing Woods",
    15032: "Golden Troupe",
    15031: "Marechaussee Hunter",
    15030: "Vourukasha's Glow",
    15029: "Nymph's Dream",
    15028: "Flower of Paradise Lost",
    15027: "Desert Pavilion Chronicle",
    15026: "Gilded Dreams",
    15025: "Deepwood Memories",
    15024: "Echoes of an Offering",
    15023: "Vermillion Hereafter",
    15022: "Husk of Opulent Dreams",
    15021: "Ocean-Hued Clam",
    15020: "Emblem of Severed Fate",
    15019: "Shimenawa's Reminiscence",
    15018: "Tenacity of the Millelith",
    15017: "Pale Flame",
    15007: "Noblesse Oblige",
    15002: "Viridescent Venerer",
    15001: "Gladiator's Finale",
    15003: "Wanderer's Troupe",
    15005: "Crimson Witch of Flames",
    15006: "Thundering Fury",
    15008: "Bloodstained Chivalry",
    15009: "Archaic Petra",
    15010: "Retracing Bolide",
    15011: "Blizzard Strayer",
    15012: "Heart of Depth",
}

# Weapon ItemId or Icon Name map
WEAPON_NAME_MAP: Dict[int, Tuple[str, str, int]] = {
    # Polearms
    13512: ("Crimson Moon's Semblance", "Polearm", 5),
    13511: ("Staff of the Scarlet Sands", "Polearm", 5),
    13509: ("Engulfing Lightning", "Polearm", 5),
    13507: ("Calamity Queller", "Polearm", 5),
    13501: ("Staff of Homa", "Polearm", 5),
    13502: ("Skyward Spine", "Polearm", 5),
    13505: ("Primordial Jade Winged-Spear", "Polearm", 5),
    13415: ("\"The Catch\"", "Polearm", 4),
    13407: ("Favonius Lance", "Polearm", 4),
    13401: ("Dragon's Bane", "Polearm", 4),
    13403: ("Deathmatch", "Polearm", 4),
    12502: ("Footprint of the Rainbow", "Polearm", 4),
    # Swords
    11512: ("Splendor of Tranquil Waters", "Sword", 5),
    11509: ("Mistsplitter Reforged", "Sword", 5),
    11503: ("Freedom-Sworn", "Sword", 5),
    11502: ("Skyward Blade", "Sword", 5),
    11501: ("Aquila Favonia", "Sword", 5),
    11413: ("Fleuve Cendre Ferryman", "Sword", 4),
    11418: ("Xiphos' Moonlight", "Sword", 4),
    11401: ("Favonius Sword", "Sword", 4),
    11402: ("Sacrificial Sword", "Sword", 4),
    11403: ("The Flute", "Sword", 4),
    11405: ("Lion's Roar", "Sword", 4),
    11412: ("Toukabou Shigure", "Sword", 4),
    11432: ("Earth Shaker", "Sword", 4),
    # Bows
    15509: ("Aqua Simulacra", "Bow", 5),
    15503: ("Elegy for the End", "Bow", 5),
    15501: ("Skyward Harp", "Bow", 5),
    15502: ("Amos' Bow", "Bow", 5),
    15508: ("Polar Star", "Bow", 5),
    15511: ("The First Great Magic", "Bow", 5),
    15512: ("Silvershower Heartstrings", "Bow", 5),
    15401: ("Favonius Warbow", "Bow", 4),
    15402: ("Stringless", "Bow", 4),
    15403: ("Sacrificial Bow", "Bow", 4),
    14302: ("Slingshot", "Bow", 3),
    # Catalysts
    14512: ("Tome of the Eternal Flow", "Catalyst", 5),
    14506: ("A Thousand Floating Dreams", "Catalyst", 5),
    14509: ("Kagura's Verity", "Catalyst", 5),
    14501: ("Skyward Atlas", "Catalyst", 5),
    14502: ("Lost Prayer to the Sacred Winds", "Catalyst", 5),
    14406: ("Prototype Amber", "Catalyst", 4),
    14402: ("Sacrificial Fragments", "Catalyst", 4),
    14401: ("Favonius Codex", "Catalyst", 4),
    14403: ("The Widsith", "Catalyst", 4),
    12426: ("Oathsworn Eye", "Catalyst", 4),
    14434: ("Ring of Yaxche", "Catalyst", 4),
    # Claymores
    12510: ("Beacon of the Reed Sea", "Claymore", 5),
    12511: ("Verdict", "Claymore", 5),
    12501: ("Skyward Pride", "Claymore", 5),
    12503: ("Wolf's Gravestone", "Claymore", 5),
    12504: ("Song of Broken Pines", "Claymore", 5),
    12505: ("Redhorn Stonethresher", "Claymore", 5),
    12401: ("Favonius Greatsword", "Claymore", 4),
    12402: ("Sacrificial Greatsword", "Claymore", 4),
    12409: ("Serpent Spine", "Claymore", 4),
    12426: ("Tidal Shadow", "Claymore", 4),
}


def get_character_info(avatar_id: int) -> Tuple[str, str, int]:
    """Retrieve canonical character name, element, and rarity by avatar ID."""
    if avatar_id in CHARACTER_DATABASE:
        return CHARACTER_DATABASE[avatar_id]
    return (f"Character_{avatar_id}", "Unknown", 5)


def resolve_weapon_name(item_id: int, fallback_name: str, icon_str: Optional[str] = None) -> Tuple[str, str, int]:
    """Resolve weapon canonical name, weapon type, and rarity."""
    if item_id in WEAPON_NAME_MAP:
        return WEAPON_NAME_MAP[item_id]
    # Fallback to cleaned fallback_name or icon parsing
    if fallback_name and not fallback_name.isdigit():
        return (fallback_name, "Weapon", 4)
    return (f"Weapon_{item_id}", "Weapon", 4)


def resolve_artifact_set_name(set_hash_or_id: Any, fallback_name: str, icon_str: Optional[str] = None) -> str:
    """Resolve artifact canonical set name."""
    # Check if icon has RelicIcon_XXXXX
    if icon_str and "RelicIcon_" in icon_str:
        try:
            set_id = int(icon_str.split("RelicIcon_")[1].split("_")[0])
            if set_id in ARTIFACT_SET_MAP:
                return ARTIFACT_SET_MAP[set_id]
        except Exception:
            pass

    if str(set_hash_or_id).isdigit() and int(set_hash_or_id) in ARTIFACT_SET_MAP:
        return ARTIFACT_SET_MAP[int(set_hash_or_id)]

    if fallback_name and not fallback_name.isdigit():
        return fallback_name

    return "Artifact Set"


def format_stat_value(stat_key: str, value: float) -> Tuple[str, str, bool]:
    """
    Format a stat value appropriately given its key.
    Returns (human_name, formatted_string, is_percent).
    """
    info = FIGHT_PROP_INFO.get(stat_key)
    if info:
        name, is_percent = info
    else:
        is_percent = ("PERCENT" in stat_key or "RATE" in stat_key or "HURT" in stat_key or "CRITICAL" in stat_key or "EFFICIENCY" in stat_key)
        name = stat_key.replace("FIGHT_PROP_", "").replace("_", " ").title()

    if is_percent:
        if value < 2.0 and value > 0:
            formatted = f"{value * 100:.1f}%"
        else:
            formatted = f"{value:.1f}%"
    else:
        formatted = f"{round(value):,}" if value >= 10 else f"{value:.1f}"

    return name, formatted, is_percent
