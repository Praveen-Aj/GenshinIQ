"""
Deterministic Build & Stat Engine for GenshinIQ (Phase 7).
Pure mathematical calculation layer for character scaling, weapon stats,
artifact contributions, set bonuses, derived combat attributes, and build comparisons.
"""

import json
import logging
import math
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union

from backend.models.stat_engine import (
    CalculationStatus,
    StatSourceType,
    StatContribution,
    AttributeBreakdown,
    SlotArtifactBreakdown,
    SetBonusActivation,
    FullStatBreakdown,
    CalculatedCombatStats,
    CharacterBuildSnapshot,
    BuildComparison,
    VersionCompatibilityStatus,
)
from backend.services.account_inventory_service import account_inventory_service
from backend.services.game_data_service import game_data_service
from backend.services.version_service import version_service, parse_version_tuple

logger = logging.getLogger(__name__)

# Dynamically resolved canonical game data version driving calculations
def get_canonical_dataset_version() -> str:
    """Return the active canonical dataset version currently driving calculations."""
    try:
        from backend.services.canonical_data_pipeline import canonical_data_pipeline
        return canonical_data_pipeline.get_active_version()
    except Exception:
        return "7.0"

CANONICAL_DATASET_VERSION = get_canonical_dataset_version()

# Standard 5-Star Artifact Main Stat Progression Tables (Lv 0 to Lv 20)
ARTIFACT_5STAR_MAIN_STATS: Dict[str, Tuple[float, float]] = {
    # stat_key: (lv0_val, lv20_val)
    "hp": (717.0, 4780.0),          # Flower flat HP
    "atk": (47.0, 311.0),           # Plume flat ATK
    "hp_": (0.070, 0.466),          # Sands/Goblet/Circlet HP%
    "atk_": (0.070, 0.466),         # Sands/Goblet/Circlet ATK%
    "def_": (0.087, 0.583),         # Sands/Goblet/Circlet DEF%
    "enerRech_": (0.078, 0.518),    # Sands ER%
    "eleMas": (28.0, 187.0),        # Sands/Goblet/Circlet EM (Canonical 187 at +20)
    "critRate_": (0.047, 0.311),    # Circlet CRIT Rate%
    "critDMG_": (0.093, 0.622),     # Circlet CRIT DMG%
    "heal_": (0.054, 0.359),        # Circlet Healing Bonus%
    "physical_dmg_": (0.087, 0.583),# Goblet Physical DMG%
    "pyro_dmg_": (0.070, 0.466),    # Goblet Pyro DMG%
    "hydro_dmg_": (0.070, 0.466),   # Goblet Hydro DMG%
    "electro_dmg_": (0.070, 0.466), # Goblet Electro DMG%
    "anemo_dmg_": (0.070, 0.466),   # Goblet Anemo DMG%
    "cryo_dmg_": (0.070, 0.466),    # Goblet Cryo DMG%
    "geo_dmg_": (0.070, 0.466),     # Goblet Geo DMG%
    "dendro_dmg_": (0.070, 0.466),  # Goblet Dendro DMG%
}

# 4-Star Artifact Main Stat Progression Tables (Lv 0 to Lv 16)
ARTIFACT_4STAR_MAIN_STATS: Dict[str, Tuple[float, float]] = {
    "hp": (645.0, 3571.0),
    "atk": (42.0, 232.0),
    "hp_": (0.063, 0.348),
    "atk_": (0.063, 0.348),
    "def_": (0.079, 0.435),
    "enerRech_": (0.070, 0.387),
    "eleMas": (25.0, 139.0),        # Canonical 139 at +16
    "critRate_": (0.042, 0.232),
    "critDMG_": (0.084, 0.464),
    "heal_": (0.048, 0.268),
    "physical_dmg_": (0.079, 0.435),
    "pyro_dmg_": (0.063, 0.348),
    "hydro_dmg_": (0.063, 0.348),
    "electro_dmg_": (0.063, 0.348),
    "anemo_dmg_": (0.063, 0.348),
    "cryo_dmg_": (0.063, 0.348),
    "geo_dmg_": (0.063, 0.348),
    "dendro_dmg_": (0.063, 0.348),
}

# Standard 2-Piece Artifact Set Bonuses
CANONICAL_2PC_BONUSES: Dict[str, Dict[str, float]] = {
    "gladiator's finale": {"atk_": 0.18},
    "shimenawa's reminiscence": {"atk_": 0.18},
    "vermillion hereafter": {"atk_": 0.18},
    "echoes of an offering": {"atk_": 0.18},
    "nighttime whispers in the echoing woods": {"atk_": 0.18},
    "fragment of harmonic whimsey": {"atk_": 0.18},
    "unfinished reverie": {"atk_": 0.18},
    "viridescent venerer": {"anemo_dmg_": 0.15},
    "crimson witch of flames": {"pyro_dmg_": 0.15},
    "blizzard strayer": {"cryo_dmg_": 0.15},
    "thundering fury": {"electro_dmg_": 0.15},
    "heart of depth": {"hydro_dmg_": 0.15},
    "archaic petra": {"geo_dmg_": 0.15},
    "deepwood memories": {"dendro_dmg_": 0.15},
    "nymph's dream": {"hydro_dmg_": 0.15},
    "vourukasha's glow": {"hp_": 0.20},
    "tenacity of the millelith": {"hp_": 0.20},
    "husk of opulent dreams": {"def_": 0.30},
    "emblem of severed fate": {"enerRech_": 0.20},
    "wanderer's troupe": {"eleMas": 80.0},
    "gilded dreams": {"eleMas": 80.0},
    "flower of paradise lost": {"eleMas": 80.0},
    "noblesse oblige": {"burst_dmg_": 0.20},
    "golden troupe": {"skill_dmg_": 0.20},
    "marechaussee hunter": {"normal_charged_dmg_": 0.15},
    "song of days past": {"heal_": 0.15},
    "ocean-hued clam": {"heal_": 0.15},
    "maiden beloved": {"heal_": 0.15},
    "pale flame": {"physical_dmg_": 0.25},
    "bloodstained chivalry": {"physical_dmg_": 0.25},
}


class WeaponPassiveClassification:
    """Canonical classification separating static sheet stats from combat-only effects."""
    def __init__(
        self,
        weapon_name: str,
        unconditional_stats: Dict[str, List[float]],
        conditional_combat_effects: List[str]
    ):
        self.weapon_name = weapon_name
        self.unconditional_stats = unconditional_stats
        self.conditional_combat_effects = conditional_combat_effects


CANONICAL_WEAPON_PASSIVE_REGISTRY: Dict[str, WeaponPassiveClassification] = {
    "staff of homa": WeaponPassiveClassification(
        weapon_name="Staff of Homa",
        unconditional_stats={"hp_": [0.20, 0.25, 0.30, 0.35, 0.40]},
        conditional_combat_effects=[
            "Provides an ATK Bonus based on 0.8% of wielder's Max HP",
            "When HP < 50%, ATK Bonus increased by additional 1.0% of Max HP"
        ]
    ),
    "primordial jade cutter": WeaponPassiveClassification(
        weapon_name="Primordial Jade Cutter",
        unconditional_stats={"hp_": [0.20, 0.25, 0.30, 0.35, 0.40]},
        conditional_combat_effects=[
            "Provides an ATK Bonus based on 1.2% of wielder's Max HP"
        ]
    ),
    "calamity queller": WeaponPassiveClassification(
        weapon_name="Calamity Queller",
        unconditional_stats={"all_elemental_dmg_": [0.12, 0.15, 0.18, 0.21, 0.24]},
        conditional_combat_effects=[
            "Gain Consummation for 20s after using Elemental Skill, increasing ATK by 3.2% per second (max 6 stacks)",
            "When off-field, Consummation ATK increase is doubled"
        ]
    ),
    "mistsplitter reforged": WeaponPassiveClassification(
        weapon_name="Mistsplitter Reforged",
        unconditional_stats={"all_elemental_dmg_": [0.12, 0.15, 0.18, 0.21, 0.24]},
        conditional_combat_effects=[
            "Gain 8/16/28% Elemental DMG at 1/2/3 stacks of Mistsplitter's Might (Normal Attack Elemental DMG, Burst cast, Energy < 100%)"
        ]
    ),
    "freedom-sworn": WeaponPassiveClassification(
        weapon_name="Freedom-Sworn",
        unconditional_stats={"all_dmg_": [0.10, 0.125, 0.15, 0.175, 0.20]},
        conditional_combat_effects=[
            "Millennial Movement: Song of Resistance: Increases Normal/Charged/Plunging Attack DMG by 16-32% and ATK by 20-40% upon triggering 2 reactions"
        ]
    ),
    "the widsith": WeaponPassiveClassification(
        weapon_name="The Widsith",
        unconditional_stats={},
        conditional_combat_effects=[
            "Recitative: ATK +60-120% for 10s",
            "Aria: All Elemental DMG +48-96% for 10s",
            "Interlude: Elemental Mastery +240-480 for 10s"
        ]
    ),
}


def round_half_up(val: float) -> int:
    """
    Standard arithmetic rounding (round half up) matching in-game integer stat display.
    Guarantees that .5 values round up (e.g. 186.5 -> 187, 220.5 -> 221) rather than
    suffering from IEEE 754 banker's round-half-to-even bias.
    """
    return int(math.floor(val + 0.5))


class StatEngineService:
    """
    Core Deterministic Build & Stat Engine Service.
    Resolves base layers, gear contributions, set bonuses, derived stats, and comparisons.
    """

    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.raw_avatars_dir = self.root_dir / "data" / "raw" / "game_data" / "avatars"
        self.raw_weapons_dir = self.root_dir / "data" / "raw" / "game_data" / "weapons"
        self.avatar_curves_file = self.root_dir / "data" / "processed" / "game_data" / "avatar_curves.json"
        self.weapon_curves_file = self.root_dir / "data" / "processed" / "game_data" / "weapon_curves.json"
        self.artifact_levels_file = self.root_dir / "data" / "processed" / "game_data" / "artifact_levels.json"
        self._avatar_cache: Dict[str, Dict[str, Any]] = {}
        self._weapon_cache: Dict[str, Dict[str, Any]] = {}
        self.avatar_curves: Dict[str, Dict[str, float]] = {}
        self.weapon_curves: Dict[str, Dict[str, float]] = {}
        self.artifact_levels: Dict[str, Dict[str, Dict[str, float]]] = {}
        self._load_caches()

    def _load_caches(self):
        """Index raw avatar and weapon JSON files and canonical curves for O(1) mathematical lookup."""
        if self.avatar_curves_file.exists():
            try:
                with open(self.avatar_curves_file, "r", encoding="utf-8") as f:
                    self.avatar_curves = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load avatar curves: {e}")

        if self.weapon_curves_file.exists():
            try:
                with open(self.weapon_curves_file, "r", encoding="utf-8") as f:
                    self.weapon_curves = json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load weapon curves: {e}")

        if self.artifact_levels_file.exists():
            try:
                with open(self.artifact_levels_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        self.artifact_levels = data
                    else:
                        self.artifact_levels = {}
            except Exception as e:
                logger.warning(f"Failed to load artifact levels: {e}")

        if self.raw_avatars_dir.exists():
            for f in self.raw_avatars_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        raw = json.load(jf).get("data", {})
                    aid = str(raw.get("id", ""))
                    name = raw.get("name", "").lower()
                    self._avatar_cache[aid] = raw
                    if name:
                        self._avatar_cache[name] = raw
                except Exception as e:
                    logger.warning(f"Failed to load raw avatar {f.name}: {e}")

        if self.raw_weapons_dir.exists():
            for f in self.raw_weapons_dir.glob("*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        raw = json.load(jf).get("data", {})
                    wid = str(raw.get("id", ""))
                    name = raw.get("name", "").lower()
                    self._weapon_cache[wid] = raw
                    if name:
                        self._weapon_cache[name] = raw
                except Exception as e:
                    logger.warning(f"Failed to load raw weapon {f.name}: {e}")

    # ==========================================================================
    # 0. CANONICAL VERSION ENFORCEMENT & COMPATIBILITY
    # ==========================================================================

    @property
    def canonical_dataset_version(self) -> str:
        """Dynamically resolve active canonical dataset version driving calculations."""
        return get_canonical_dataset_version()

    def evaluate_version_compatibility(
        self,
        requested_version: Optional[str],
        character_name: Optional[str] = None,
        weapon_name: Optional[str] = None,
        is_pure_engine_constant: bool = False,
    ) -> Tuple[CalculationStatus, VersionCompatibilityStatus, List[str], str]:
        """
        Evaluate compatibility between requested game version and canonical dataset version (v5.4).

        Execution Path:
        VersionService -> requested calculation version -> canonical dataset compatibility -> StatEngine -> calculation status

        Rules & Semantics:
        - MISSING_VERSION_METADATA: requested_version is None, empty, or "missing" -> (PARTIAL, MISSING_VERSION_METADATA, warnings, '5.4')
        - VERIFIED_COMPATIBLE: Mathematically/static engine constant genuinely independent of game version -> (COMPLETE, VERIFIED_COMPATIBLE, warnings, clean_ver)
        - UNKNOWN_COMPATIBILITY: requested_version is "unknown" or invalid format -> (UNSUPPORTED, UNKNOWN_COMPATIBILITY, warnings, clean_ver)
        - UNSUPPORTED_FUTURE: requested_version is unreleased or not recognized in registry -> (UNSUPPORTED, UNSUPPORTED_FUTURE, warnings, clean_ver)
        - MATCHING: clean_ver <= '5.4' -> (COMPLETE, MATCHING, warnings, clean_ver)
        - STALE_INTERVENING_CHANGES: clean_ver > '5.4' and conflicting changes exist in registry -> (PARTIAL, STALE_INTERVENING_CHANGES, warnings, clean_ver)
        - PROJECT_REGISTRY_COMPATIBLE: clean_ver > '5.4' and no conflicting changes in project registry (direct target data unavailable) -> (COMPLETE, PROJECT_REGISTRY_COMPATIBLE, warnings, clean_ver)
        """
        dataset_ver = self.canonical_dataset_version

        if requested_version is None or str(requested_version).strip() == "" or str(requested_version).lower() in ("none", "missing"):
            return (
                CalculationStatus.PARTIAL,
                VersionCompatibilityStatus.MISSING_VERSION_METADATA,
                ["Missing version metadata: target calculation version was not specified; canonical version compatibility cannot be verified."],
                dataset_ver
            )

        clean_ver = str(requested_version).strip().lstrip("v")

        # Category A: Pure mathematical/static engine constants that genuinely do not depend on game version
        if is_pure_engine_constant:
            return (
                CalculationStatus.COMPLETE,
                VersionCompatibilityStatus.VERIFIED_COMPATIBLE,
                [f"Mathematical engine constant verified as invariant across all game versions (v{clean_ver})."],
                clean_ver
            )

        if clean_ver.lower() == "unknown" or not (clean_ver and clean_ver[0].isdigit()):
            return (
                CalculationStatus.UNSUPPORTED,
                VersionCompatibilityStatus.UNKNOWN_COMPATIBILITY,
                [f"Target game version '{requested_version}' has unknown compatibility status; cannot be verified against canonical dataset or project registry."],
                clean_ver
            )

        gv = version_service.get_version(clean_ver)

        if not gv:
            return (
                CalculationStatus.UNSUPPORTED,
                VersionCompatibilityStatus.UNSUPPORTED_FUTURE,
                [f"Target game version v{clean_ver} is unrecognized in canonical patch registry. Calculations for unknown future versions are UNSUPPORTED."],
                clean_ver
            )

        if not gv.is_released or gv.is_upcoming:
            return (
                CalculationStatus.UNSUPPORTED,
                VersionCompatibilityStatus.UNSUPPORTED_FUTURE,
                [f"Target game version v{clean_ver} ('{gv.name}') is an unreleased/future patch. Calculations on unreleased versions are UNSUPPORTED."],
                clean_ver
            )

        req_tuple = parse_version_tuple(clean_ver)
        dataset_tuple = parse_version_tuple(dataset_ver)

        if req_tuple <= dataset_tuple:
            # Case A: matching or within verified dataset scope
            return (
                CalculationStatus.COMPLETE,
                VersionCompatibilityStatus.MATCHING,
                [f"Calculation executed with canonical data verified for v{clean_ver}."],
                clean_ver
            )

        # Case B: requested version is newer than dataset
        changed_systems = version_service.get_changed_systems_between(dataset_ver, clean_ver)
        conflicts = []
        if character_name and character_name in changed_systems:
            conflicts.append(f"Character '{character_name}'")
        if weapon_name and weapon_name in changed_systems:
            conflicts.append(f"Weapon '{weapon_name}'")
        if "Base Stats" in changed_systems or "Stat Scaling" in changed_systems:
            conflicts.append("Core Stat Scaling Formulas")

        if conflicts:
            return (
                CalculationStatus.PARTIAL,
                VersionCompatibilityStatus.STALE_INTERVENING_CHANGES,
                [f"Target calculation affected by patch changes between v{dataset_ver} and v{clean_ver}: {conflicts}. Core scaling may be superseded."],
                clean_ver
            )

        # Compatible via project-maintained registry
        return (
            CalculationStatus.COMPLETE,
            VersionCompatibilityStatus.PROJECT_REGISTRY_COMPATIBLE,
            [f"Canonical numerical dataset verified through v{dataset_ver}. Compatible with target v{clean_ver} via project-maintained patch registry (zero conflicting system modifications recorded in registry; direct v{clean_ver} game client data is unavailable)."],
            clean_ver
        )

    # ==========================================================================
    # 1. CHARACTER STAT ENGINE
    # ==========================================================================

    def resolve_character_base_stats(
        self,
        character_name_or_id: Union[str, int],
        level: int = 90,
        ascension: int = 6
    ) -> Tuple[Dict[str, float], Dict[str, float], CalculationStatus, List[str]]:
        """
        Deterministically resolve character base stats (HP, ATK, DEF) and ascension special stat.
        Returns: (base_stats, ascension_stats, status, warnings)
        """
        warnings: List[str] = []
        status = CalculationStatus.COMPLETE

        # Bounds validation
        if not (1 <= level <= 90) or not (0 <= ascension <= 6):
            return (
                {"hp": 0.0, "atk": 0.0, "def_": 0.0},
                {},
                CalculationStatus.INVALID,
                [f"Invalid character level ({level}) or ascension ({ascension})"]
            )

        key = str(character_name_or_id).lower()
        raw_avatar = self._avatar_cache.get(key)
        canonical_char = game_data_service.get_character(key)

        if not raw_avatar and not canonical_char:
            return (
                {"hp": 0.0, "atk": 0.0, "def_": 0.0},
                {},
                CalculationStatus.UNSUPPORTED,
                [f"Character '{character_name_or_id}' not found in canonical database"]
            )

        # Base level 90 shortcut from canonical verified database
        if level == 90 and ascension == 6 and canonical_char:
            base_stats = {
                "hp": canonical_char.base_hp_lvl90,
                "atk": canonical_char.base_atk_lvl90,
                "def_": canonical_char.base_def_lvl90,
            }
            ascension_stats = {}
            if canonical_char.ascension_stat and canonical_char.ascension_stat_val_lvl90:
                s_name = canonical_char.ascension_stat
                val_str = canonical_char.ascension_stat_val_lvl90.replace("%", "").strip()
                try:
                    num_val = float(val_str)
                    if "%" in canonical_char.ascension_stat_val_lvl90 or num_val < 1.0:
                        ascension_stats[s_name] = num_val / 100.0 if num_val > 1.0 else num_val
                    else:
                        ascension_stats[s_name] = num_val
                except ValueError:
                    ascension_stats[s_name] = 0.0
            return base_stats, ascension_stats, status, warnings

        # Detailed mathematical calculation using raw curves and promote tables
        if raw_avatar:
            upgrade = raw_avatar.get("upgrade", {})
            props = {p["propType"]: p for p in upgrade.get("prop", [])}
            promotes = upgrade.get("promote", [])

            # Get promote bonus for requested ascension
            promote_idx = min(ascension, len(promotes) - 1) if promotes else 0
            p_data = promotes[promote_idx] if promotes else {}
            add_props = p_data.get("addProps") or {}

            hp_prop = props.get("FIGHT_PROP_BASE_HP", {})
            atk_prop = props.get("FIGHT_PROP_BASE_ATTACK", {})
            def_prop = props.get("FIGHT_PROP_BASE_DEFENSE", {})

            init_hp = hp_prop.get("initValue", 1000.0)
            init_atk = atk_prop.get("initValue", 25.0)
            init_def = def_prop.get("initValue", 60.0)

            hp_c_name = hp_prop.get("type", "GROW_CURVE_HP_S5")
            atk_c_name = atk_prop.get("type", "GROW_CURVE_ATTACK_S5")
            def_c_name = def_prop.get("type", hp_c_name)

            hp_curve = self.avatar_curves.get(hp_c_name, {})
            atk_curve = self.avatar_curves.get(atk_c_name, {})
            def_curve = self.avatar_curves.get(def_c_name, hp_curve)

            hp_mult = hp_curve.get(str(level), hp_curve.get(level, 1.0))
            atk_mult = atk_curve.get(str(level), atk_curve.get(level, 1.0))
            def_mult = def_curve.get(str(level), def_curve.get(level, hp_mult))

            bonus_hp = add_props.get("FIGHT_PROP_BASE_HP", 0.0)
            bonus_atk = add_props.get("FIGHT_PROP_BASE_ATTACK", 0.0)
            bonus_def = add_props.get("FIGHT_PROP_BASE_DEFENSE", 0.0)

            base_hp = round_half_up(init_hp * hp_mult + bonus_hp)
            base_atk = round_half_up(init_atk * atk_mult + bonus_atk)
            base_def = round_half_up(init_def * def_mult + bonus_def)

            ascension_stats = {}
            for prop_k, prop_v in add_props.items():
                if prop_k not in ["FIGHT_PROP_BASE_HP", "FIGHT_PROP_BASE_ATTACK", "FIGHT_PROP_BASE_DEFENSE"]:
                    human_name = prop_k.replace("FIGHT_PROP_", "").replace("_", " ").title()
                    if prop_k == "FIGHT_PROP_ELEMENT_MASTERY":
                        human_name = "Elemental Mastery"
                    elif prop_k == "FIGHT_PROP_CRITICAL_HURT":
                        human_name = "CRIT DMG"
                    elif prop_k == "FIGHT_PROP_CRITICAL":
                        human_name = "CRIT Rate"
                    elif prop_k == "FIGHT_PROP_CHARGE_EFFICIENCY":
                        human_name = "Energy Recharge"
                    ascension_stats[human_name] = prop_v

            return {"hp": float(base_hp), "atk": float(base_atk), "def_": float(base_def)}, ascension_stats, status, warnings

        # Fallback if raw avatar missing
        warnings.append("Raw avatar promote curves unavailable; used canonical level 90 anchor")
        return (
            {"hp": canonical_char.base_hp_lvl90, "atk": canonical_char.base_atk_lvl90, "def_": canonical_char.base_def_lvl90},
            {},
            CalculationStatus.PARTIAL,
            warnings
        )

    # ==========================================================================
    # 2. WEAPON STAT ENGINE
    # ==========================================================================

    def resolve_weapon_stats(
        self,
        weapon_name_or_id: Union[str, int],
        level: int = 90,
        ascension: int = 6,
        refinement: int = 1
    ) -> Tuple[float, Optional[str], float, Dict[str, float], CalculationStatus, List[str]]:
        """
        Deterministically resolve weapon base ATK, secondary stat, and static passive stats.
        Returns: (base_atk, sub_stat_name, sub_stat_val, static_passives, status, warnings)
        """
        warnings: List[str] = []
        status = CalculationStatus.COMPLETE

        if not (1 <= level <= 90) or not (0 <= ascension <= 6) or not (1 <= refinement <= 5):
            return 0.0, None, 0.0, {}, CalculationStatus.INVALID, [f"Invalid weapon params (Lv{level}, Asc{ascension}, R{refinement})"]

        key = str(weapon_name_or_id).lower()
        raw_weapon = self._weapon_cache.get(key)
        canonical_weapon = game_data_service.get_weapon(key)

        if not raw_weapon and not canonical_weapon:
            return 0.0, None, 0.0, {}, CalculationStatus.UNSUPPORTED, [f"Weapon '{weapon_name_or_id}' not found"]

        # Resolve via exact canonical weapon curves if raw definition available
        if raw_weapon:
            upgrade = raw_weapon.get("upgrade", {})
            props = upgrade.get("prop", [])
            promotes = upgrade.get("promote", [])

            promote_idx = min(ascension, len(promotes) - 1) if promotes else 0
            p_data = promotes[promote_idx] if promotes else {}
            add_props = p_data.get("addProps") or {}

            base_atk = 0.0
            if len(props) > 0:
                atk_prop = props[0]
                init_atk = atk_prop.get("initValue", 42.0)
                atk_curve_name = atk_prop.get("type", "GROW_CURVE_ATTACK_101")
                atk_mult = self.weapon_curves.get(atk_curve_name, {}).get(str(level), 1.0)
                bonus_atk = add_props.get("FIGHT_PROP_BASE_ATTACK", 0.0)
                base_atk = float(round_half_up(init_atk * atk_mult + bonus_atk))

            sub_name = None
            sub_val = 0.0
            if len(props) > 1:
                sub_prop = props[1]
                prop_key = sub_prop.get("propType")
                prop_map = {
                    "FIGHT_PROP_ELEMENT_MASTERY": "Elemental Mastery",
                    "FIGHT_PROP_CRITICAL_HURT": "CRIT DMG",
                    "FIGHT_PROP_CRITICAL": "CRIT Rate",
                    "FIGHT_PROP_CHARGE_EFFICIENCY": "Energy Recharge",
                    "FIGHT_PROP_ATTACK_PERCENT": "ATK%",
                    "FIGHT_PROP_HP_PERCENT": "HP%",
                    "FIGHT_PROP_DEFENSE_PERCENT": "DEF%",
                    "FIGHT_PROP_PHYSICAL_ADD_HURT": "Physical DMG Bonus",
                }
                sub_name = prop_map.get(prop_key, prop_key)
                init_sub = sub_prop.get("initValue", 0.0)
                sub_curve_name = sub_prop.get("type", "GROW_CURVE_CRITICAL_101")
                sub_mult = self.weapon_curves.get(sub_curve_name, {}).get(str(level), 1.0)
                calculated_sub = init_sub * sub_mult

                if prop_key == "FIGHT_PROP_ELEMENT_MASTERY" or sub_name == "Elemental Mastery":
                    # Elemental Mastery is a flat integer stat in Genshin Impact (arithmetic round half up)
                    sub_val = float(round_half_up(calculated_sub))
                elif calculated_sub <= 1.0:
                    # Percentage stat: preserve precision e.g. 0.661536 for exact 66.2% display
                    sub_val = round(calculated_sub, 6)
                else:
                    sub_val = round(calculated_sub, 1)

            # Resolve static unconditional passives from canonical registry
            static_passives: Dict[str, float] = {}
            w_name_clean = canonical_weapon.name.lower() if canonical_weapon else key
            passive_def = CANONICAL_WEAPON_PASSIVE_REGISTRY.get(w_name_clean)
            if passive_def:
                for stat_k, values in passive_def.unconditional_stats.items():
                    r_idx = min(max(refinement - 1, 0), len(values) - 1)
                    static_passives[stat_k] = values[r_idx]

            return base_atk, sub_name, sub_val, static_passives, status, warnings

        # Fallback if raw weapon missing but canonical summary available
        if canonical_weapon:
            base_atk = canonical_weapon.base_atk_lvl90 if level >= 90 else canonical_weapon.base_atk_lvl1
            sub_name = canonical_weapon.sub_stat_type
            sub_val = 0.0
            if canonical_weapon.sub_stat_val_lvl90:
                s_str = canonical_weapon.sub_stat_val_lvl90.replace("%", "").strip()
                try:
                    num_val = float(s_str)
                    if sub_name == "Elemental Mastery":
                        sub_val = float(round(num_val))
                    elif "%" in canonical_weapon.sub_stat_val_lvl90:
                        sub_val = num_val / 100.0
                    else:
                        sub_val = num_val
                except ValueError:
                    sub_val = 0.0
            return base_atk, sub_name, sub_val, {}, CalculationStatus.PARTIAL, ["Raw weapon curves missing; used milestone values"]

        return 0.0, None, 0.0, {}, CalculationStatus.UNSUPPORTED, ["Weapon data missing"]

    # ==========================================================================
    # 3. ARTIFACT STAT ENGINE
    # ==========================================================================

    def resolve_artifact_main_stat(
        self,
        slot: str,
        main_stat_key: str,
        rarity: int = 5,
        level: int = 20,
        explicit_value: Optional[float] = None
    ) -> Tuple[str, float]:
        """
        Deterministically resolve artifact main stat name and exact numeric value.
        """
        # If client / GOOD snapshot already has explicit value, respect it
        name_map = {
            "hp": "HP",
            "hp_": "HP%",
            "atk": "ATK",
            "atk_": "ATK%",
            "def_": "DEF%",
            "eleMas": "Elemental Mastery",
            "enerRech_": "Energy Recharge",
            "critRate_": "CRIT Rate",
            "critDMG_": "CRIT DMG",
            "heal_": "Healing Bonus",
            "physical_dmg_": "Physical DMG Bonus",
            "pyro_dmg_": "Pyro DMG Bonus",
            "hydro_dmg_": "Hydro DMG Bonus",
            "electro_dmg_": "Electro DMG Bonus",
            "anemo_dmg_": "Anemo DMG Bonus",
            "cryo_dmg_": "Cryo DMG Bonus",
            "geo_dmg_": "Geo DMG Bonus",
            "dendro_dmg_": "Dendro DMG Bonus",
        }
        human_name = name_map.get(main_stat_key, main_stat_key)

        if explicit_value is not None and explicit_value > 0.0:
            return human_name, explicit_value

        # Calculate from exact canonical progression tables
        max_lvl = 20 if rarity == 5 else (16 if rarity == 4 else 12)
        clamped_lvl = min(max(level, 0), max_lvl)

        # 1. Exact lookup from canonical artifact levels
        rarity_data = self.artifact_levels.get(str(rarity), {}) if isinstance(self.artifact_levels, dict) else {}
        lvl_data = rarity_data.get(str(clamped_lvl), {}) if isinstance(rarity_data, dict) else {}
        if main_stat_key in lvl_data:
            raw_val = lvl_data[main_stat_key]
            if main_stat_key in ["hp", "atk"]:
                return human_name, float(round_half_up(raw_val))
            elif main_stat_key == "eleMas":
                # Arithmetic display rounding (e.g. 186.5 -> 187, 139.3 -> 139)
                return human_name, float(round_half_up(raw_val))
            else:
                return human_name, round(raw_val, 4)

        # 2. Fallback to static progression table if exact JSON missing
        table = ARTIFACT_5STAR_MAIN_STATS if rarity == 5 else ARTIFACT_4STAR_MAIN_STATS
        if main_stat_key in table:
            lv0, lv_max = table[main_stat_key]
            ratio = clamped_lvl / float(max_lvl)
            val = lv0 + (lv_max - lv0) * ratio
            if main_stat_key in ["hp", "atk", "eleMas"]:
                val = float(round_half_up(val))
            else:
                val = round(val, 4)
            return human_name, val

        return human_name, 0.0

    def resolve_artifact_inventory_contribution(
        self,
        artifact_instances: List[Dict[str, Any]]
    ) -> Tuple[List[SlotArtifactBreakdown], List[SetBonusActivation], float]:
        """
        Processes a list of equipped artifact instances:
        - Resolves main stats and substats per slot.
        - Calculates individual and total artifact Crit Value (CV).
        - Computes active 2-piece and 4-piece set bonuses.
        """
        slot_breakdowns: List[SlotArtifactBreakdown] = []
        set_counts: Dict[str, int] = {}
        total_cv = 0.0

        for art in artifact_instances:
            slot = art.get("slot", "unknown")
            set_name = art.get("canonical_set_name") or art.get("set_name") or "Unknown Set"
            rarity = art.get("rarity", 5)
            level = art.get("level", 20)
            main_key = art.get("main_stat_key", "hp" if slot == "flower" else "atk" if slot == "plume" else "atk_")
            explicit_main_val = art.get("main_stat_value")

            main_name, main_val = self.resolve_artifact_main_stat(
                slot=slot,
                main_stat_key=main_key,
                rarity=rarity,
                level=level,
                explicit_value=explicit_main_val
            )

            # Substats & piece CV
            substats = art.get("substats", [])
            piece_cr = 0.0
            piece_cd = 0.0
            for s in substats:
                s_k = s.get("key", "")
                s_v = float(s.get("value", 0.0))
                if s_k == "critRate_":
                    piece_cr += s_v
                elif s_k == "critDMG_":
                    piece_cd += s_v

            piece_cv = round(2.0 * piece_cr + piece_cd, 1)
            total_cv += piece_cv

            slot_breakdowns.append(
                SlotArtifactBreakdown(
                    account_instance_id=art.get("account_instance_id"),
                    slot=slot,
                    set_name=set_name,
                    rarity=rarity,
                    level=level,
                    main_stat_key=main_key,
                    main_stat_name=main_name,
                    main_stat_value=main_val,
                    substats=substats,
                    crit_value=piece_cv,
                )
            )

            # Track set piece count
            s_clean = set_name.lower().strip()
            set_counts[s_clean] = set_counts.get(s_clean, 0) + 1

        # Check Set Bonuses
        active_bonuses: List[SetBonusActivation] = []
        for set_clean, count in set_counts.items():
            if count >= 2:
                stats_2pc = CANONICAL_2PC_BONUSES.get(set_clean, {})
                # Look up 2pc description from canonical DB
                desc = "2-Piece Set Bonus"
                art_entry = game_data_service.get_artifact_set(set_clean)
                if art_entry and art_entry.bonus_2pc:
                    desc = art_entry.bonus_2pc

                active_bonuses.append(
                    SetBonusActivation(
                        set_name=art_entry.name if art_entry else set_clean.title(),
                        pieces_active=2,
                        bonus_description=desc,
                        is_character_sheet_stat=True,
                        character_sheet_stats=stats_2pc,
                        combat_modifiers=[],
                        applied_stats=stats_2pc,
                    )
                )

            if count >= 4:
                desc_4pc = "4-Piece Set Bonus"
                art_entry = game_data_service.get_artifact_set(set_clean)
                if art_entry and art_entry.bonus_4pc:
                    desc_4pc = art_entry.bonus_4pc

                active_bonuses.append(
                    SetBonusActivation(
                        set_name=art_entry.name if art_entry else set_clean.title(),
                        pieces_active=4,
                        bonus_description=desc_4pc,
                        is_character_sheet_stat=False,
                        character_sheet_stats={},
                        combat_modifiers=[desc_4pc],
                        applied_stats={},  # 4pc bonuses are predominantly conditional in combat
                    )
                )

        return slot_breakdowns, active_bonuses, round(total_cv, 1)

    # ==========================================================================
    # 4. AGGREGATION & DERIVED COMBAT ATTRIBUTES
    # ==========================================================================

    def calculate_build_stats(
        self,
        character_name_or_id: Union[str, int],
        char_level: int = 90,
        char_ascension: int = 6,
        char_constellation: int = 0,
        weapon_name_or_id: Optional[Union[str, int]] = None,
        weapon_level: int = 90,
        weapon_ascension: int = 6,
        weapon_refinement: int = 1,
        artifacts: Optional[List[Dict[str, Any]]] = None,
        talents: Optional[Dict[str, int]] = None,
        game_version: Optional[str] = None,
    ) -> CharacterBuildSnapshot:
        """
        Main entry point for calculating full deterministic stats, breakdown, and build snapshot.
        """
        all_warnings: List[str] = []
        overall_status = CalculationStatus.COMPLETE

        char_name_str = str(character_name_or_id)
        w_name_str = str(weapon_name_or_id) if weapon_name_or_id else None

        # 0. Canonical Version Compatibility Check (VersionService integration)
        v_status, v_compat, v_warnings, eff_version = self.evaluate_version_compatibility(
            game_version, character_name=char_name_str, weapon_name=w_name_str
        )
        all_warnings.extend(v_warnings)
        if v_status != CalculationStatus.COMPLETE:
            overall_status = v_status

        # 1. Resolve Character Base Layer
        char_base, char_asc, c_status, c_warn = self.resolve_character_base_stats(
            character_name_or_id, level=char_level, ascension=char_ascension
        )
        all_warnings.extend(c_warn)
        if c_status != CalculationStatus.COMPLETE:
            overall_status = c_status

        # 2. Resolve Weapon Layer
        w_base_atk = 0.0
        w_sub_name = None
        w_sub_val = 0.0
        w_passives: Dict[str, float] = {}
        weapon_info = None

        if weapon_name_or_id:
            w_base_atk, w_sub_name, w_sub_val, w_passives, w_status, w_warn = self.resolve_weapon_stats(
                weapon_name_or_id, level=weapon_level, ascension=weapon_ascension, refinement=weapon_refinement
            )
            all_warnings.extend(w_warn)
            if w_status != CalculationStatus.COMPLETE and overall_status == CalculationStatus.COMPLETE:
                overall_status = w_status

            weapon_info = {
                "name": str(weapon_name_or_id),
                "level": weapon_level,
                "ascension": weapon_ascension,
                "refinement": weapon_refinement,
                "base_atk": w_base_atk,
                "secondary_stat_name": w_sub_name,
                "secondary_stat_val": w_sub_val,
                "static_passives": w_passives,
            }

        # 3. Resolve Artifact Layer
        artifacts_list = artifacts or []
        art_slots, art_set_bonuses, total_cv = self.resolve_artifact_inventory_contribution(artifacts_list)

        # 4. Prepare Aggregation Containers
        hp_bd = AttributeBreakdown(base_value=char_base["hp"])
        atk_bd = AttributeBreakdown(base_value=char_base["atk"] + w_base_atk)
        def_bd = AttributeBreakdown(base_value=char_base["def_"])
        cr_bd = AttributeBreakdown(base_value=0.05)   # Default 5% CRIT Rate
        cd_bd = AttributeBreakdown(base_value=0.50)   # Default 50% CRIT DMG
        er_bd = AttributeBreakdown(base_value=1.00)   # Default 100% ER
        em_bd = AttributeBreakdown(base_value=0.0)    # Default 0 EM
        heal_bd = AttributeBreakdown(base_value=0.0)
        shield_bd = AttributeBreakdown(base_value=0.0)
        dmg_bonuses: Dict[str, AttributeBreakdown] = {}

        # Log Character Base Contributions
        char_name_str = str(character_name_or_id)
        hp_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Base", source_type=StatSourceType.CHARACTER_BASE, stat_name="Base HP", value=char_base["hp"]))
        atk_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Base", source_type=StatSourceType.CHARACTER_BASE, stat_name="Base ATK", value=char_base["atk"]))
        def_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Base", source_type=StatSourceType.CHARACTER_BASE, stat_name="Base DEF", value=char_base["def_"]))
        cr_bd.contributions.append(StatContribution(source_name="Baseline Rule", source_type=StatSourceType.GENERIC_PASSIVE, stat_name="Base CRIT Rate", value=0.05, is_percentage=True))
        cd_bd.contributions.append(StatContribution(source_name="Baseline Rule", source_type=StatSourceType.GENERIC_PASSIVE, stat_name="Base CRIT DMG", value=0.50, is_percentage=True))
        er_bd.contributions.append(StatContribution(source_name="Baseline Rule", source_type=StatSourceType.GENERIC_PASSIVE, stat_name="Base Energy Recharge", value=1.00, is_percentage=True))

        if weapon_name_or_id:
            atk_bd.contributions.append(StatContribution(source_name=f"{weapon_info['name']} Base", source_type=StatSourceType.WEAPON_BASE, stat_name="Weapon Base ATK", value=w_base_atk))

        # Add Character Ascension Stat
        for a_stat, a_val in char_asc.items():
            s_lower = a_stat.lower()
            if "crit rate" in s_lower:
                cr_bd.percent_bonus += a_val
                cr_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="CRIT Rate", value=a_val, is_percentage=True))
            elif "crit dmg" in s_lower:
                cd_bd.percent_bonus += a_val
                cd_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="CRIT DMG", value=a_val, is_percentage=True))
            elif "energy recharge" in s_lower:
                er_bd.percent_bonus += a_val
                er_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="Energy Recharge", value=a_val, is_percentage=True))
            elif "elemental mastery" in s_lower:
                em_bd.flat_bonus += a_val
                em_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="Elemental Mastery", value=a_val))
            elif "hp" in s_lower and "%" in a_stat:
                hp_bd.percent_bonus += a_val
                hp_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="HP%", value=a_val, is_percentage=True))
            elif "atk" in s_lower and "%" in a_stat:
                atk_bd.percent_bonus += a_val
                atk_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="ATK%", value=a_val, is_percentage=True))
            elif "def" in s_lower and "%" in a_stat:
                def_bd.percent_bonus += a_val
                def_bd.contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name="DEF%", value=a_val, is_percentage=True))
            elif "dmg bonus" in s_lower:
                elem = a_stat.replace("DMG Bonus", "").strip()
                if elem not in dmg_bonuses:
                    dmg_bonuses[elem] = AttributeBreakdown()
                dmg_bonuses[elem].percent_bonus += a_val
                dmg_bonuses[elem].contributions.append(StatContribution(source_name=f"{char_name_str} Ascension", source_type=StatSourceType.CHARACTER_ASCENSION, stat_name=a_stat, value=a_val, is_percentage=True))

        # Add Weapon Secondary Stat
        if w_sub_name and w_sub_val > 0.0:
            s_lower = w_sub_name.lower()
            w_label = weapon_info["name"] if weapon_info else "Weapon"
            if "crit rate" in s_lower:
                cr_bd.percent_bonus += w_sub_val
                cr_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="CRIT Rate", value=w_sub_val, is_percentage=True))
            elif "crit dmg" in s_lower:
                cd_bd.percent_bonus += w_sub_val
                cd_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="CRIT DMG", value=w_sub_val, is_percentage=True))
            elif "energy recharge" in s_lower:
                er_bd.percent_bonus += w_sub_val
                er_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="Energy Recharge", value=w_sub_val, is_percentage=True))
            elif "elemental mastery" in s_lower:
                em_bd.flat_bonus += w_sub_val
                em_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="Elemental Mastery", value=w_sub_val))
            elif "atk" in s_lower:
                atk_bd.percent_bonus += w_sub_val
                atk_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="ATK%", value=w_sub_val, is_percentage=True))
            elif "hp" in s_lower:
                hp_bd.percent_bonus += w_sub_val
                hp_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="HP%", value=w_sub_val, is_percentage=True))
            elif "def" in s_lower:
                def_bd.percent_bonus += w_sub_val
                def_bd.contributions.append(StatContribution(source_name=f"{w_label} Secondary", source_type=StatSourceType.WEAPON_SECONDARY, stat_name="DEF%", value=w_sub_val, is_percentage=True))

        # Add Weapon Static Passives
        for p_k, p_v in w_passives.items():
            w_label = weapon_info["name"] if weapon_info else "Weapon"
            if p_k == "hp_":
                hp_bd.percent_bonus += p_v
                hp_bd.contributions.append(StatContribution(source_name=f"{w_label} Passive", source_type=StatSourceType.WEAPON_PASSIVE, stat_name="HP%", value=p_v, is_percentage=True))
            elif p_k == "all_elemental_dmg_":
                for elem in ["Pyro", "Hydro", "Electro", "Anemo", "Cryo", "Geo", "Dendro"]:
                    if elem not in dmg_bonuses:
                        dmg_bonuses[elem] = AttributeBreakdown()
                    dmg_bonuses[elem].percent_bonus += p_v
                    dmg_bonuses[elem].contributions.append(StatContribution(source_name=f"{w_label} Passive", source_type=StatSourceType.WEAPON_PASSIVE, stat_name=f"{elem} DMG Bonus", value=p_v, is_percentage=True))

        # Add Artifact Main Stats and Substats
        for art_slot in art_slots:
            slot_label = f"{art_slot.slot.title()} ({art_slot.set_name})"
            m_key = art_slot.main_stat_key
            m_val = art_slot.main_stat_value

            if m_key == "hp":
                hp_bd.flat_bonus += m_val
                hp_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="Flat HP", value=m_val))
            elif m_key == "atk":
                atk_bd.flat_bonus += m_val
                atk_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="Flat ATK", value=m_val))
            elif m_key == "hp_":
                hp_bd.percent_bonus += m_val
                hp_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="HP%", value=m_val, is_percentage=True))
            elif m_key == "atk_":
                atk_bd.percent_bonus += m_val
                atk_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="ATK%", value=m_val, is_percentage=True))
            elif m_key == "def_":
                def_bd.percent_bonus += m_val
                def_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="DEF%", value=m_val, is_percentage=True))
            elif m_key == "enerRech_":
                er_bd.percent_bonus += m_val
                er_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="Energy Recharge", value=m_val, is_percentage=True))
            elif m_key == "eleMas":
                em_bd.flat_bonus += m_val
                em_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="Elemental Mastery", value=m_val))
            elif m_key == "critRate_":
                cr_bd.percent_bonus += m_val
                cr_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="CRIT Rate", value=m_val, is_percentage=True))
            elif m_key == "critDMG_":
                cd_bd.percent_bonus += m_val
                cd_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="CRIT DMG", value=m_val, is_percentage=True))
            elif m_key == "heal_":
                heal_bd.percent_bonus += m_val
                heal_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name="Healing Bonus", value=m_val, is_percentage=True))
            elif "dmg_" in m_key:
                elem = m_key.replace("_dmg_", "").title()
                if elem not in dmg_bonuses:
                    dmg_bonuses[elem] = AttributeBreakdown()
                dmg_bonuses[elem].percent_bonus += m_val
                dmg_bonuses[elem].contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_MAIN, stat_name=f"{elem} DMG Bonus", value=m_val, is_percentage=True))

            # Process substats
            for sub in art_slot.substats:
                s_k = sub.get("key", "")
                s_v = float(sub.get("value", 0.0))
                # Percentage vs Flat
                if s_k == "hp_":
                    hp_bd.percent_bonus += (s_v / 100.0)
                    hp_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="HP%", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "atk_":
                    atk_bd.percent_bonus += (s_v / 100.0)
                    atk_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="ATK%", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "def_":
                    def_bd.percent_bonus += (s_v / 100.0)
                    def_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="DEF%", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "critRate_":
                    cr_bd.percent_bonus += (s_v / 100.0)
                    cr_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="CRIT Rate", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "critDMG_":
                    cd_bd.percent_bonus += (s_v / 100.0)
                    cd_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="CRIT DMG", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "enerRech_":
                    er_bd.percent_bonus += (s_v / 100.0)
                    er_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="Energy Recharge", value=(s_v / 100.0), is_percentage=True))
                elif s_k == "eleMas":
                    em_bd.flat_bonus += s_v
                    em_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="Elemental Mastery", value=s_v))
                elif s_k == "hp":
                    hp_bd.flat_bonus += s_v
                    hp_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="Flat HP", value=s_v))
                elif s_k == "atk":
                    atk_bd.flat_bonus += s_v
                    atk_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="Flat ATK", value=s_v))
                elif s_k == "def":
                    def_bd.flat_bonus += s_v
                    def_bd.contributions.append(StatContribution(source_name=slot_label, source_type=StatSourceType.ARTIFACT_SUBSTAT, stat_name="Flat DEF", value=s_v))

        # Add Active 2-Piece Set Bonuses
        for sb in art_set_bonuses:
            if sb.pieces_active == 2 and sb.applied_stats:
                set_src = f"2pc {sb.set_name}"
                for s_key, s_val in sb.applied_stats.items():
                    if s_key == "atk_":
                        atk_bd.percent_bonus += s_val
                        atk_bd.contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name="ATK%", value=s_val, is_percentage=True))
                    elif s_key == "hp_":
                        hp_bd.percent_bonus += s_val
                        hp_bd.contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name="HP%", value=s_val, is_percentage=True))
                    elif s_key == "def_":
                        def_bd.percent_bonus += s_val
                        def_bd.contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name="DEF%", value=s_val, is_percentage=True))
                    elif s_key == "enerRech_":
                        er_bd.percent_bonus += s_val
                        er_bd.contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name="Energy Recharge", value=s_val, is_percentage=True))
                    elif s_key == "eleMas":
                        em_bd.flat_bonus += s_val
                        em_bd.contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name="Elemental Mastery", value=s_val))
                    elif "dmg_" in s_key:
                        elem = s_key.replace("_dmg_", "").title()
                        if elem not in dmg_bonuses:
                            dmg_bonuses[elem] = AttributeBreakdown()
                        dmg_bonuses[elem].percent_bonus += s_val
                        dmg_bonuses[elem].contributions.append(StatContribution(source_name=set_src, source_type=StatSourceType.ARTIFACT_SET_2PC, stat_name=f"{elem} DMG Bonus", value=s_val, is_percentage=True))

        # 5. Final Derived Calculations (Exact Game Arithmetic)
        hp_bd.final_value = round(hp_bd.base_value * (1.0 + hp_bd.percent_bonus) + hp_bd.flat_bonus)
        atk_bd.final_value = round(atk_bd.base_value * (1.0 + atk_bd.percent_bonus) + atk_bd.flat_bonus)
        def_bd.final_value = round(def_bd.base_value * (1.0 + def_bd.percent_bonus) + def_bd.flat_bonus)
        cr_bd.final_value = round(cr_bd.base_value + cr_bd.percent_bonus, 4)
        cd_bd.final_value = round(cd_bd.base_value + cd_bd.percent_bonus, 4)
        er_bd.final_value = round(er_bd.base_value + er_bd.percent_bonus, 4)
        em_bd.final_value = round(em_bd.base_value + em_bd.flat_bonus)
        heal_bd.final_value = round(heal_bd.percent_bonus, 4)
        shield_bd.final_value = round(shield_bd.percent_bonus, 4)

        final_dmg_bonuses: Dict[str, float] = {}
        for elem, bd in dmg_bonuses.items():
            bd.final_value = round(bd.percent_bonus, 4)
            final_dmg_bonuses[elem] = bd.final_value

        full_breakdown = FullStatBreakdown(
            hp=hp_bd,
            atk=atk_bd,
            def_=def_bd,
            crit_rate=cr_bd,
            crit_dmg=cd_bd,
            energy_recharge=er_bd,
            elemental_mastery=em_bd,
            healing_bonus=heal_bd,
            shield_strength=shield_bd,
            damage_bonuses=dmg_bonuses,
            artifact_slots=art_slots,
            active_set_bonuses=art_set_bonuses,
            total_artifact_crit_value=total_cv,
        )

        combat_stats = CalculatedCombatStats(
            hp=hp_bd.final_value,
            base_hp=hp_bd.base_value,
            atk=atk_bd.final_value,
            base_atk=atk_bd.base_value,
            def_=def_bd.final_value,
            base_def=def_bd.base_value,
            crit_rate=cr_bd.final_value,
            crit_dmg=cd_bd.final_value,
            energy_recharge=er_bd.final_value,
            elemental_mastery=em_bd.final_value,
            healing_bonus=heal_bd.final_value,
            shield_strength=shield_bd.final_value,
            damage_bonuses=final_dmg_bonuses,
        )

        # Retrieve canonical ID if available
        canonical_char = game_data_service.get_character(char_name_str.lower())

        return CharacterBuildSnapshot(
            character_name=canonical_char.name if canonical_char else char_name_str,
            canonical_id=canonical_char.id if canonical_char else None,
            level=char_level,
            ascension=char_ascension,
            constellation=char_constellation,
            talents=talents or {},
            weapon=weapon_info,
            artifacts=[a.model_dump() for a in art_slots],
            stats=combat_stats,
            breakdown=full_breakdown,
            calculation_status=overall_status,
            warnings=all_warnings,
            game_version=eff_version,
            dataset_version=self.canonical_dataset_version,
            version_compatibility=v_compat,
        )

    # ==========================================================================
    # 5. ACCOUNT INTEGRATION & COMPARISONS
    # ==========================================================================

    def get_account_character_build(
        self,
        character_name_or_id: Union[str, int],
        game_version: Optional[str] = None,
    ) -> Optional[CharacterBuildSnapshot]:
        """
        Retrieves the build snapshot for an owned character using the Phase 6 normalized account snapshot.
        """
        snapshot = account_inventory_service.get_active_snapshot()
        if not snapshot:
            return None

        # 1. Locate character in account
        q_lower = str(character_name_or_id).lower()
        char_inst = next(
            (c for c in snapshot.characters if c.canonical_name.lower() == q_lower or (c.canonical_id and str(c.canonical_id) == q_lower) or c.good_key.lower() == q_lower),
            None
        )
        if not char_inst:
            return None

        # 2. Locate equipped weapon
        equipped_weapon = next(
            (w for w in snapshot.weapons if w.location and w.location.lower() == char_inst.canonical_name.lower()),
            None
        )

        # 3. Locate equipped artifacts
        equipped_artifacts = [
            a.model_dump() for a in snapshot.artifacts if a.location and a.location.lower() == char_inst.canonical_name.lower()
        ]

        w_name = equipped_weapon.canonical_name if equipped_weapon else None
        w_lvl = equipped_weapon.level if equipped_weapon else 90
        w_asc = equipped_weapon.ascension if equipped_weapon else 6
        w_ref = equipped_weapon.refinement if equipped_weapon else 1

        return self.calculate_build_stats(
            character_name_or_id=char_inst.canonical_name,
            char_level=char_inst.level,
            char_ascension=char_inst.ascension,
            char_constellation=char_inst.constellation,
            weapon_name_or_id=w_name,
            weapon_level=w_lvl,
            weapon_ascension=w_asc,
            weapon_refinement=w_ref,
            artifacts=equipped_artifacts,
            talents=char_inst.talent_levels,
            game_version=game_version,
        )

    def compare_builds(
        self,
        build_a: CharacterBuildSnapshot,
        build_b: CharacterBuildSnapshot
    ) -> BuildComparison:
        """
        Deterministic comparison primitive between two builds.
        Computes delta: (Build B - Build A).
        """
        deltas: Dict[str, float] = {
            "hp": round(build_b.stats.hp - build_a.stats.hp, 1),
            "atk": round(build_b.stats.atk - build_a.stats.atk, 1),
            "def_": round(build_b.stats.def_ - build_a.stats.def_, 1),
            "crit_rate": round(build_b.stats.crit_rate - build_a.stats.crit_rate, 4),
            "crit_dmg": round(build_b.stats.crit_dmg - build_a.stats.crit_dmg, 4),
            "energy_recharge": round(build_b.stats.energy_recharge - build_a.stats.energy_recharge, 4),
            "elemental_mastery": round(build_b.stats.elemental_mastery - build_a.stats.elemental_mastery, 1),
        }
        cv_delta = round(
            build_b.breakdown.total_artifact_crit_value - build_a.breakdown.total_artifact_crit_value, 1
        )

        notes: List[str] = []
        if deltas["atk"] > 0:
            notes.append(f"Build B gains +{deltas['atk']} ATK")
        elif deltas["atk"] < 0:
            notes.append(f"Build B loses {abs(deltas['atk'])} ATK")

        if deltas["crit_rate"] > 0 or deltas["crit_dmg"] > 0:
            notes.append(f"CRIT changes: CR {deltas['crit_rate']:+.1%}, CD {deltas['crit_dmg']:+.1%}")

        if cv_delta != 0:
            notes.append(f"Artifact CV delta: {cv_delta:+.1f} CV")

        return BuildComparison(
            build_a_name=f"{build_a.character_name} (Lv{build_a.level})",
            build_b_name=f"{build_b.character_name} (Lv{build_b.level})",
            stat_deltas=deltas,
            crit_value_delta=cv_delta,
            summary_notes=notes,
        )


# Singleton instance
stat_engine_service = StatEngineService()
