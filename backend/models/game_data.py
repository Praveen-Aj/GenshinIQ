"""Pydantic models for canonical structured Genshin Impact game data."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class TalentSkill(BaseModel):
    """Character talent / skill information."""
    name: str
    unlock: str = Field(..., description="Normal Attack, Elemental Skill, Elemental Burst, or Passive")
    type: str = Field(default="skill", description="normal, skill, burst, or passive")
    description: str
    icon: Optional[str] = None


class Constellation(BaseModel):
    """Character constellation information."""
    level: int = Field(..., ge=1, le=6)
    name: str
    description: str
    icon: Optional[str] = None


class CharacterData(BaseModel):
    """Canonical Genshin Impact character model."""
    id: int
    name: str
    title: Optional[str] = None
    element: str = Field(..., description="Pyro, Hydro, Anemo, Electro, Dendro, Cryo, Geo")
    weapon_type: str = Field(..., description="Sword, Claymore, Polearm, Bow, Catalyst")
    rarity: int = Field(..., ge=4, le=5)
    region: Optional[str] = None
    affiliation: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    base_hp_lvl90: float
    base_atk_lvl90: float
    base_def_lvl90: float
    ascension_stat: str
    ascension_stat_val_lvl90: str
    talents: List[TalentSkill] = Field(default_factory=list)
    constellations: List[Constellation] = Field(default_factory=list)
    ascension_materials: List[str] = Field(default_factory=list)
    talent_materials: List[str] = Field(default_factory=list)


class WeaponData(BaseModel):
    """Canonical Genshin Impact weapon model."""
    id: int
    name: str
    weapon_type: str = Field(..., description="Sword, Claymore, Polearm, Bow, Catalyst")
    rarity: int = Field(..., ge=1, le=5)
    icon: Optional[str] = None
    base_atk_lvl1: float
    base_atk_lvl90: float
    sub_stat_type: Optional[str] = None
    sub_stat_val_lvl90: Optional[str] = None
    passive_name: Optional[str] = None
    passive_desc: Optional[str] = None
    refinements: List[str] = Field(default_factory=list, description="Descriptions for R1-R5")
    ascension_materials: List[str] = Field(default_factory=list)


class ArtifactPiece(BaseModel):
    """Individual piece in an artifact set."""
    slot: str = Field(..., description="flower, plume, sands, goblet, circlet")
    name: str
    icon: Optional[str] = None


class ArtifactSetData(BaseModel):
    """Canonical Genshin Impact artifact set model."""
    id: int
    name: str
    rarities: List[int] = Field(default_factory=lambda: [4, 5])
    icon: Optional[str] = None
    bonus_2pc: str
    bonus_4pc: Optional[str] = None
    pieces: Dict[str, str] = Field(default_factory=dict, description="slot -> piece name")


class MaterialData(BaseModel):
    """Canonical Genshin Impact item/material model."""
    id: int
    name: str
    type: str = Field(..., description="Ascension Gem, Boss Material, Talent Book, Weapon Material, Local Specialty")
    rarity: int = Field(default=3, ge=1, le=5)
    description: Optional[str] = None
    sources: List[str] = Field(default_factory=list)


class SearchResult(BaseModel):
    """Search hit model across all game data categories."""
    id: int
    name: str
    category: str = Field(..., description="character, weapon, artifact, material")
    element_or_type: Optional[str] = None
    rarity: int
    description: Optional[str] = None
