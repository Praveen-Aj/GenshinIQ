"""Pydantic models for normalized Genshin Impact account and build data."""

from enum import Enum
from typing import Dict, List, Optional
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
