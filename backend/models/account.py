"""Pydantic models for normalized Genshin Impact account and build data."""

from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field


class ArtifactSlot(str, Enum):
    FLOWER = "flower"
    PLUME = "plume"
    SANDS = "sands"
    GOBLET = "goblet"
    CIRCLET = "circlet"


class StatValue(BaseModel):
    """Normalized stat with key, raw value, and formatted string."""
    key: str = Field(
        ...,
        description="Internal stat ID, e.g., FIGHT_PROP_CRITICAL"
    )
    name: str = Field(
        ...,
        description="Human-readable stat name, e.g., CRIT Rate"
    )
    value: float = Field(..., description="Raw numerical value")
    formatted: str = Field(
        ...,
        description="Formatted string: e.g., 68.4%"
    )
    is_percent: bool = Field(
        default=False,
        description="Whether the stat is represented as a percentage"
    )


class Substat(BaseModel):
    """Individual artifact substat roll."""
    key: str
    name: str
    value: float
    formatted: str
    is_percent: bool = False
    rolls: int = Field(
        default=1,
        description="Estimated number of substat upgrades"
    )


class ArtifactData(BaseModel):
    """Normalized artifact equipment item."""
    item_id: int
    name: str
    slot: ArtifactSlot
    set_id: Optional[int] = None
    set_name: str
    icon: Optional[str] = None
    rarity: int = Field(
        ...,
        ge=1,
        le=5,
        description="Artifact star rarity (1-5)"
    )
    level: int = Field(
        ...,
        ge=0,
        le=20,
        description="Artifact level (0-20)"
    )
    main_stat: StatValue
    substats: List[Substat] = Field(default_factory=list)


class WeaponData(BaseModel):
    """Normalized weapon equipment item."""
    item_id: int
    name: str
    weapon_type: str = Field(
        default="Unknown",
        description="Sword, Claymore, Polearm, Bow, Catalyst"
    )
    rarity: int = Field(default=4, ge=1, le=5)
    level: int = Field(..., ge=1, le=90)
    ascension: int = Field(default=0, ge=0, le=6)
    refinement: int = Field(default=1, ge=1, le=5)
    icon: Optional[str] = None
    base_atk: Optional[float] = None
    sub_stat: Optional[StatValue] = None


class TalentData(BaseModel):
    """Normalized talent/skill data."""
    skill_id: int
    name: str = Field(default="Skill")
    skill_type: str = Field(
        default="skill",
        description="normal, skill, burst, or passive"
    )
    level: int = Field(..., ge=1, le=15)
    boosted_level: int = Field(
        ...,
        ge=1,
        le=15,
        description="Effective level with constellation boosts"
    )
    icon: Optional[str] = None


class CombatStats(BaseModel):
    """Normalized aggregated combat stats for a character build."""
    max_hp: float = 0.0
    base_hp: float = 0.0
    atk: float = 0.0
    base_atk: float = 0.0
    defense: float = 0.0
    base_def: float = 0.0
    crit_rate: float = 0.05
    crit_dmg: float = 0.50
    energy_recharge: float = 1.00
    elemental_mastery: float = 0.0
    healing_bonus: float = 0.0
    shield_strength: float = 0.0
    damage_bonuses: Dict[str, float] = Field(
        default_factory=dict,
        description="e.g. {'Pyro': 0.466, 'Physical': 0.0}"
    )


class CharacterBuild(BaseModel):
    """Complete build info for a character in player's showcase."""
    avatar_id: int
    name: str
    element: str = Field(
        default="Unknown",
        description="Pyro, Hydro, Anemo, Electro, Dendro, Cryo, Geo"
    )
    rarity: int = Field(default=5, ge=4, le=5)
    level: int = Field(..., ge=1, le=90)
    ascension: int = Field(default=0, ge=0, le=6)
    constellation: int = Field(default=0, ge=0, le=6)
    fetter_level: int = Field(
        default=10,
        ge=1,
        le=10,
        description="Friendship level"
    )
    icon: Optional[str] = None
    costume_id: Optional[int] = None
    talents: List[TalentData] = Field(default_factory=list)
    weapon: Optional[WeaponData] = None
    artifacts: List[ArtifactData] = Field(default_factory=list)
    stats: CombatStats = Field(default_factory=CombatStats)
    raw_fight_prop_map: Dict[str, float] = Field(default_factory=dict)


class PlayerProfile(BaseModel):
    """Player public account profile overview from Enka."""
    uid: str
    nickname: str = "Traveler"
    level: int = Field(default=1, description="Adventure Rank (AR)")
    world_level: int = Field(default=0, description="World Level")
    signature: Optional[str] = None
    achievement_count: int = 0
    spiral_abyss_floor: Optional[int] = None
    spiral_abyss_chamber: Optional[int] = None
    avatar_icon: Optional[str] = None
    name_card_id: Optional[int] = None
    showcase_character_ids: List[int] = Field(default_factory=list)


class EnkaShowcaseResponse(BaseModel):
    """Top-level normalized response returned by account service."""
    profile: PlayerProfile
    characters: List[CharacterBuild] = Field(default_factory=list)
    character_count: int = 0
    ttl: int = Field(default=300, description="Cache TTL in seconds")
    cached: bool = False
    fetched_at: str


# ==============================================================================
# Phase 6: GOOD v3 Account Inventory Models
# ==============================================================================

class ResolutionStatus(str, Enum):
    """Entity resolution status against canonical game database."""
    EXACT_MATCH = "EXACT_MATCH"
    ALIAS_MATCH = "ALIAS_MATCH"
    LEGACY_MATCH = "LEGACY_MATCH"
    UNRESOLVED = "UNRESOLVED"


class SnapshotMetadata(BaseModel):
    """Metadata describing a specific imported account snapshot."""
    imported_at: str = Field(..., description="ISO UTC timestamp of the import")
    good_version: int = Field(default=3, description="GOOD schema version")
    source: str = Field(default="Inventory_Kamera", description="Exporter source application")
    source_file_hash: str = Field(..., description="SHA-256 hash of the raw import payload")
    parser_version: str = Field(default="1.0.0", description="Version of the GOOD v3 parser")
    account_uid: Optional[str] = Field(default=None, description="Account UID if provided by export")
    character_count: int = 0
    weapon_count: int = 0
    artifact_count: int = 0
    material_count: int = 0
    unresolved_count: int = 0


class UnresolvedRecord(BaseModel):
    """Record of an entity from GOOD that could not be resolved to canonical game data."""
    category: str = Field(..., description="character, weapon, artifact, material")
    good_key: str = Field(..., description="Original key as given in GOOD payload")
    details: Dict[str, Any] = Field(default_factory=dict, description="Raw fields preserved from import")
    reason: str = Field(default="Not found in canonical database", description="Explanation for resolution failure")


class AccountCharacterInstance(BaseModel):
    """Normalized representation of a character owned in the player's account inventory."""
    canonical_id: Optional[int] = Field(default=None, description="Canonical character ID")
    canonical_name: str = Field(..., description="Canonical character name (e.g. Kaedehara Kazuha)")
    good_key: str = Field(..., description="Original GOOD key (e.g. KaedeharaKazuha)")
    element: Optional[str] = None
    rarity: Optional[int] = None
    weapon_type: Optional[str] = None
    level: int = Field(..., ge=1, le=90, description="Character level")
    ascension: int = Field(default=0, ge=0, le=6, description="Ascension phase")
    constellation: int = Field(default=0, ge=0, le=6, description="Unlocked constellation level")
    talent_levels: Dict[str, int] = Field(default_factory=dict, description="Talents e.g. {'auto': 1, 'skill': 10, 'burst': 8}")
    resolution_status: ResolutionStatus = ResolutionStatus.EXACT_MATCH


class AccountWeaponInstance(BaseModel):
    """
    An individual weapon instance owned in the player's account.
    Multiple copies of the same weapon (e.g. 16 copies of Dragon's Bane) are distinct instances.
    """
    account_instance_id: str = Field(..., description="Deterministic unique instance identifier (e.g. weapon_good_34)")
    canonical_id: Optional[int] = Field(default=None, description="Canonical weapon ID (e.g. 13401)")
    canonical_name: str = Field(..., description="Canonical weapon name (e.g. Dragon's Bane)")
    good_key: str = Field(..., description="GOOD weapon key (e.g. DragonsBane)")
    weapon_type: Optional[str] = None
    rarity: Optional[int] = None
    level: int = Field(..., ge=1, le=90, description="Weapon level")
    ascension: int = Field(default=0, ge=0, le=6, description="Ascension phase")
    refinement: int = Field(default=1, ge=1, le=5, description="Refinement rank")
    location: Optional[str] = Field(default=None, description="Canonical name of equipped character, or None if unequipped")
    locked: bool = Field(default=False, description="Whether weapon is locked")
    raw_id: Optional[int] = Field(default=None, description="Internal scanner ID if provided by GOOD")
    resolution_status: ResolutionStatus = ResolutionStatus.EXACT_MATCH


class AccountArtifactInstance(BaseModel):
    """
    An individual artifact instance owned in the player's account.
    Every artifact has distinct identity and preserves exact substats and rolls.
    """
    account_instance_id: str = Field(..., description="Deterministic unique instance identifier (e.g. artifact_good_0)")
    canonical_set_id: Optional[int] = Field(default=None, description="Canonical artifact set ID")
    canonical_set_name: str = Field(..., description="Canonical set name (e.g. Gladiator's Finale)")
    good_set_key: str = Field(..., description="GOOD set key (e.g. GladiatorsFinale)")
    slot: str = Field(..., description="flower, plume, sands, goblet, or circlet")
    rarity: int = Field(..., ge=1, le=5, description="Artifact star rarity")
    level: int = Field(..., ge=0, le=20, description="Artifact level")
    main_stat_key: str = Field(..., description="GOOD main stat key (e.g. atk_)")
    main_stat_name: str = Field(..., description="Human-readable main stat name (e.g. ATK%)")
    main_stat_value: Optional[float] = Field(default=None, description="Main stat value")
    substats: List[Dict[str, Any]] = Field(default_factory=list, description="List of substat dicts: [{'key': 'critRate_', 'name': 'CRIT Rate', 'value': 3.9}]")
    unactivated_substats: List[Dict[str, Any]] = Field(default_factory=list)
    location: Optional[str] = Field(default=None, description="Canonical name of equipped character, or None if in bag")
    locked: bool = Field(default=False, description="Whether artifact is locked")
    raw_id: Optional[int] = Field(default=None, description="Internal scanner ID if provided by GOOD")
    resolution_status: ResolutionStatus = ResolutionStatus.EXACT_MATCH


class AccountMaterialInstance(BaseModel):
    """A material / currency / collectible item quantity record in the account."""
    canonical_id: Optional[int] = Field(default=None, description="Canonical material ID if resolved")
    canonical_name: Optional[str] = Field(default=None, description="Canonical material name if resolved")
    good_key: str = Field(..., description="GOOD material key (e.g. Mora)")
    quantity: int = Field(..., ge=0, description="Owned quantity in inventory")
    material_type: Optional[str] = Field(default=None, description="Category: Talent Book, Weapon Material, etc.")
    rarity: Optional[int] = Field(default=None, description="Star rarity")
    resolution_status: ResolutionStatus = ResolutionStatus.EXACT_MATCH


class AccountSnapshot(BaseModel):
    """Top-level normalized account inventory snapshot representing the full user account."""
    metadata: SnapshotMetadata
    characters: List[AccountCharacterInstance] = Field(default_factory=list)
    weapons: List[AccountWeaponInstance] = Field(default_factory=list)
    artifacts: List[AccountArtifactInstance] = Field(default_factory=list)
    materials: List[AccountMaterialInstance] = Field(default_factory=list)
    unresolved_records: List[UnresolvedRecord] = Field(default_factory=list)


class AccountDiff(BaseModel):
    """Deterministic diff between two account snapshots."""
    characters_added: List[str] = Field(default_factory=list)
    characters_modified: List[Dict[str, Any]] = Field(default_factory=list)
    characters_removed: List[str] = Field(default_factory=list)
    weapons_added_count: int = 0
    weapons_removed_count: int = 0
    weapons_modified: List[Dict[str, Any]] = Field(default_factory=list)
    artifacts_added_count: int = 0
    artifacts_removed_count: int = 0
    materials_changed: Dict[str, Dict[str, int]] = Field(default_factory=dict, description="material_key -> {'old': old_qty, 'new': new_qty}")


class AccountSummary(BaseModel):
    """Deterministic inventory summary metrics."""
    total_characters: int
    built_characters_lvl90: int
    built_characters_lvl80_plus: int
    total_weapon_instances: int
    leveled_weapons_lvl90: int
    total_artifact_instances: int
    five_star_artifacts: int
    plus_20_artifacts: int
    equipped_artifacts: int
    total_material_types: int
    total_mora: int
    unresolved_material_types: int
    imported_at: str
    source_format: str

