"""
Data models and schemas for Phase 7: Deterministic Build & Stat Engine.
Provides strongly-typed models for stat breakdowns, contributions, build snapshots, and comparisons.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, ConfigDict


class CalculationStatus(str, Enum):
    """Integrity status of a deterministic stat calculation."""
    COMPLETE = "COMPLETE"          # All data verified and computed exactly
    PARTIAL = "PARTIAL"            # Non-critical passive/growth curve missing; core stats verified
    UNSUPPORTED = "UNSUPPORTED"    # Entity or level combination unsupported by canonical data
    INVALID = "INVALID"            # Impossible inputs or malformed parameters


class VersionCompatibilityStatus(str, Enum):
    """Integrity and provenance level of calculation version compatibility."""
    MATCHING = "MATCHING"                                      # Requested version matches canonical dataset version exactly (v5.4)
    VERIFIED_COMPATIBLE = "VERIFIED_COMPATIBLE"                # Mathematically/mechanically invariant engine constant
    PROJECT_REGISTRY_COMPATIBLE = "PROJECT_REGISTRY_COMPATIBLE"# Compatible based on project-maintained patch registry; direct target data unavailable
    STALE_INTERVENING_CHANGES = "STALE_INTERVENING_CHANGES"    # Conflicting patch change detected in intervening versions
    UNKNOWN_COMPATIBILITY = "UNKNOWN_COMPATIBILITY"            # Version exists but compatibility cannot be verified
    UNSUPPORTED_FUTURE = "UNSUPPORTED_FUTURE"                  # Target version is unreleased or unrecognized
    MISSING_VERSION_METADATA = "MISSING_VERSION_METADATA"      # No target version specified


class StatSourceType(str, Enum):
    """Categorized provenance source for a numerical stat contribution."""
    CHARACTER_BASE = "CHARACTER_BASE"
    CHARACTER_ASCENSION = "CHARACTER_ASCENSION"
    WEAPON_BASE = "WEAPON_BASE"
    WEAPON_SECONDARY = "WEAPON_SECONDARY"
    WEAPON_PASSIVE = "WEAPON_PASSIVE"
    ARTIFACT_MAIN = "ARTIFACT_MAIN"
    ARTIFACT_SUBSTAT = "ARTIFACT_SUBSTAT"
    ARTIFACT_SET_2PC = "ARTIFACT_SET_2PC"
    ARTIFACT_SET_4PC = "ARTIFACT_SET_4PC"
    GENERIC_PASSIVE = "GENERIC_PASSIVE"


class StatContribution(BaseModel):
    """An individual auditable contribution to a combat attribute."""
    source_name: str = Field(..., description="e.g. 'Kaedehara Kazuha Base', 'Gladiator Plume', 'Xiphos Secondary'")
    source_type: StatSourceType
    stat_name: str = Field(..., description="e.g. 'Base ATK', 'ATK%', 'Flat HP', 'CRIT Rate'")
    value: float = Field(..., description="Numeric value contributed (percentage or flat)")
    is_percentage: bool = Field(default=False)
    description: Optional[str] = None


class AttributeBreakdown(BaseModel):
    """
    Mathematical breakdown of a single combat stat into its base, percent, flat components.
    Formula: Final = Base * (1 + Sum(Percent)) + Sum(Flat)
    """
    base_value: float = Field(default=0.0, description="Base value (e.g. Char Base + Weapon Base)")
    percent_bonus: float = Field(default=0.0, description="Sum of all percentage modifiers (e.g. 0.466 for 46.6%)")
    flat_bonus: float = Field(default=0.0, description="Sum of all flat additions")
    final_value: float = Field(default=0.0, description="Final calculated attribute value")
    contributions: List[StatContribution] = Field(default_factory=list)


class SlotArtifactBreakdown(BaseModel):
    """Detailed breakdown of a single equipped artifact slot."""
    account_instance_id: Optional[str] = None
    slot: str = Field(..., description="flower, plume, sands, goblet, circlet")
    set_name: str
    rarity: int
    level: int
    main_stat_key: str
    main_stat_name: str
    main_stat_value: float
    substats: List[Dict[str, Any]] = Field(default_factory=list)
    crit_value: float = Field(default=0.0, description="2 * CRIT Rate% + CRIT DMG%")


class SetBonusActivation(BaseModel):
    """An active artifact set bonus and its applied statistical contributions."""
    set_name: str
    pieces_active: int = Field(..., ge=2, le=4)
    bonus_description: str
    is_character_sheet_stat: bool = Field(default=False, description="True if bonus directly modifies character sheet attributes (e.g. 2pc ATK +18%)")
    character_sheet_stats: Dict[str, float] = Field(default_factory=dict, description="Direct attributes added to standing character sheet")
    combat_modifiers: List[str] = Field(default_factory=list, description="Combat-only or conditional modifiers (e.g. Swirl DMG +60%, RES shred -40%)")
    applied_stats: Dict[str, float] = Field(default_factory=dict, description="Alias to character_sheet_stats for backward compatibility")


class FullStatBreakdown(BaseModel):
    """Complete auditable mathematical breakdown across all combat attributes."""
    hp: AttributeBreakdown
    atk: AttributeBreakdown
    def_: AttributeBreakdown
    crit_rate: AttributeBreakdown
    crit_dmg: AttributeBreakdown
    energy_recharge: AttributeBreakdown
    elemental_mastery: AttributeBreakdown
    healing_bonus: AttributeBreakdown
    shield_strength: AttributeBreakdown
    damage_bonuses: Dict[str, AttributeBreakdown] = Field(default_factory=dict)
    artifact_slots: List[SlotArtifactBreakdown] = Field(default_factory=list)
    active_set_bonuses: List[SetBonusActivation] = Field(default_factory=list)
    total_artifact_crit_value: float = Field(default=0.0)


class CalculatedCombatStats(BaseModel):
    """Standardized final combat attribute sheet."""
    hp: float
    base_hp: float
    atk: float
    base_atk: float
    def_: float
    base_def: float
    crit_rate: float
    crit_dmg: float
    energy_recharge: float
    elemental_mastery: float
    healing_bonus: float = 0.0
    shield_strength: float = 0.0
    damage_bonuses: Dict[str, float] = Field(default_factory=dict)


class CharacterBuildSnapshot(BaseModel):
    """
    Immutable, reproducible snapshot of a character's complete build and stats.
    Combines character identity, equipped weapon, equipped artifacts, and final derived stats.
    """
    character_name: str
    canonical_id: Optional[int] = None
    level: int = Field(..., ge=1, le=90)
    ascension: int = Field(..., ge=0, le=6)
    constellation: int = Field(default=0, ge=0, le=6)
    talents: Dict[str, int] = Field(default_factory=dict)
    weapon: Optional[Dict[str, Any]] = None
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
    stats: CalculatedCombatStats
    breakdown: FullStatBreakdown
    calculation_status: CalculationStatus = CalculationStatus.COMPLETE
    warnings: List[str] = Field(default_factory=list)
    game_version: str = Field(default="7.0", description="Target game version of the build calculation")
    dataset_version: str = Field(default="5.4", description="Canonical game data version used for base stats and curves")
    version_compatibility: VersionCompatibilityStatus = Field(
        default=VersionCompatibilityStatus.PROJECT_REGISTRY_COMPATIBLE,
        description="Version compatibility outcome: MATCHING, VERIFIED_COMPATIBLE, PROJECT_REGISTRY_COMPATIBLE, STALE_INTERVENING_CHANGES, UNKNOWN_COMPATIBILITY, UNSUPPORTED_FUTURE, MISSING_VERSION_METADATA"
    )
    build_type: str = Field(default="ACCOUNT_OWNED", description="'ACCOUNT_OWNED' or 'HYPOTHETICAL_CANONICAL'")
    is_account_grounded: bool = Field(default=True, description="True if grounded in Phase 6 account snapshot")


class BuildComparison(BaseModel):
    """Deterministic comparison primitive between two build snapshots."""
    build_a_name: str
    build_b_name: str
    stat_deltas: Dict[str, float] = Field(
        default_factory=dict,
        description="Stat differences (Build B - Build A), e.g. {'atk': +150.0, 'crit_rate': -0.05}"
    )
    crit_value_delta: float = Field(default=0.0, description="Difference in total artifact Crit Value")
    summary_notes: List[str] = Field(default_factory=list)


class CustomSubstatInput(BaseModel):
    """Client-submitted substat input with strict numerical limits."""
    model_config = ConfigDict(extra="forbid")
    key: str = Field(..., description="Canonical stat key, e.g. critRate_, critDMG_, atk_, eleMas")
    value: float = Field(..., ge=0.0, le=1000.0, description="Stat value within realistic game bounds")


class CustomArtifactInput(BaseModel):
    """
    Validated artifact specification for ad-hoc calculation.
    Arbitrary main_stat_value is strictly prohibited; derived server-side.
    """
    model_config = ConfigDict(extra="forbid")
    slot: str = Field(..., description="flower, plume, sands, goblet, circlet")
    set_name: str = Field(..., description="Canonical artifact set name")
    rarity: int = Field(default=5, ge=4, le=5)
    level: int = Field(default=20, ge=0, le=20)
    main_stat_key: str = Field(..., description="Canonical main stat key (hp, atk, hp_, atk_, def_, enerRech_, eleMas, critRate_, critDMG_, etc.)")
    substats: List[CustomSubstatInput] = Field(default_factory=list)
    account_instance_id: Optional[str] = None


class CustomBuildRequest(BaseModel):
    """
    Strictly validated request payload for POST /api/build/calculate.
    Guarantees that all base stats and scalings derive solely from canonical data.
    Arbitrary client stats (e.g. base_atk, crit_rate) are strictly forbidden.
    """
    model_config = ConfigDict(extra="forbid")
    character: str = Field(..., description="Canonical character name or numeric ID")
    level: int = Field(default=90, ge=1, le=90)
    ascension: int = Field(default=6, ge=0, le=6)
    constellation: int = Field(default=0, ge=0, le=6)
    weapon: Optional[str] = Field(default=None, description="Canonical weapon name or numeric ID")
    weapon_level: int = Field(default=90, ge=1, le=90)
    weapon_ascension: int = Field(default=6, ge=0, le=6)
    weapon_refinement: int = Field(default=1, ge=1, le=5)
    artifacts: List[CustomArtifactInput] = Field(default_factory=list)
    talents: Dict[str, int] = Field(default_factory=dict)
    account_character_instance_id: Optional[str] = Field(default=None, description="Optional account instance ID to ground in Phase 6 inventory")
    game_version: Optional[str] = Field(default=None, description="Optional target game version for calculation, e.g. '5.4' or '7.0'. If omitted, evaluated as missing version metadata (PARTIAL status).")
