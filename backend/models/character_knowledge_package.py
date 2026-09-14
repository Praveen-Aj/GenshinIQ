"""
Data models for formal Character Knowledge Packages in GenshinIQ.
Implements the finite, evidence-based GenshinIQ Knowledge Contract.
Distinguishes deterministic data, derived calculations, curated expert knowledge, and explicit knowledge gaps.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CharacterReleaseStatus(str, Enum):
    """Playable availability state of a character."""
    LIVE_RELEASED = "LIVE_RELEASED"
    UPCOMING_CONFIRMED = "UPCOMING_CONFIRMED"
    UNRELEASED_PREVIEW = "UNRELEASED_PREVIEW"
    UNKNOWN = "UNKNOWN"


class FieldQualityClassification(str, Enum):
    """Quality classification states for knowledge fields."""
    VERIFIED = "VERIFIED"
    VERIFIED_DERIVED = "VERIFIED_DERIVED"
    PARTIAL = "PARTIAL"
    MISSING = "MISSING"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class FieldQualityRecord(BaseModel):
    """Provenance and classification for an individual knowledge field."""
    field_name: str
    classification: FieldQualityClassification
    source_id: Optional[str] = None
    derivation_rule: Optional[str] = None
    notes: Optional[str] = None


class DeterministicCharacterKnowledge(BaseModel):
    """Deterministic game attributes extracted directly from canonical client data."""
    id: str
    name: str
    element: str
    weapon_type: str
    rarity: int
    region: str = "Unknown"
    release_version: str = "1.0"
    base_stats: Dict[str, Any] = Field(default_factory=dict, description="Lv 1 to Lv 90 base HP, ATK, DEF")
    ascension_stats: Dict[str, Any] = Field(default_factory=dict, description="Ascension special stat progression")
    talents: List[Dict[str, Any]] = Field(default_factory=list, description="Normal, Skill, Burst, Passives with scaling")
    constellations: List[Dict[str, Any]] = Field(default_factory=list, description="C1 to C6 definitions")
    relevant_mechanics: List[str] = Field(default_factory=list, description="ICD, gauge, nightsoul traits")


class CuratedCharacterKnowledge(BaseModel):
    """Editorial and theorycrafting knowledge from expert sources (e.g. KeqingMains)."""
    role: Optional[str] = None
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    build_priorities: List[str] = Field(default_factory=list)
    weapon_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    artifact_recommendations: List[Dict[str, Any]] = Field(default_factory=list)
    team_archetypes: List[str] = Field(default_factory=list)
    team_synergy: List[str] = Field(default_factory=list)
    rotation: Optional[str] = None
    energy_requirements: Optional[str] = None
    playstyle: Optional[str] = None
    important_mechanics: List[str] = Field(default_factory=list)
    relevant_caveats: List[str] = Field(default_factory=list)


class DerivedCalculation(BaseModel):
    """Mathematical computation deterministically derived from canonical formulas."""
    name: str
    formula: str
    inputs: Dict[str, Any]
    output: Any
    derivation_rule: str


class CharacterKnowledgePackage(BaseModel):
    """
    Complete composite knowledge package for a character.
    Contains deterministic data, curated knowledge, derived calculations, and registered gaps.
    """
    character_id: str
    character_name: str
    package_version: str = "7.0"
    target_game_version: str = "7.0"
    is_released: bool = True
    release_status: CharacterReleaseStatus = CharacterReleaseStatus.LIVE_RELEASED
    applicability_reason: Optional[str] = None
    has_canonical_data: bool = True
    has_verified_mechanics: bool = True
    has_expert_guide: bool = False
    quality_state: FieldQualityClassification = FieldQualityClassification.PARTIAL
    field_classifications: Dict[str, FieldQualityClassification] = Field(default_factory=dict)
    deterministic: DeterministicCharacterKnowledge
    curated: CuratedCharacterKnowledge
    derived_calculations: List[DerivedCalculation] = Field(default_factory=list)
    knowledge_gaps: List[str] = Field(default_factory=list, description="Cataloged missing expert fields")
    provenance_sources: List[str] = Field(default_factory=list, description="Source IDs used in compilation")
    last_verified: str = Field(default="", description="ISO timestamp of last validation pass")
