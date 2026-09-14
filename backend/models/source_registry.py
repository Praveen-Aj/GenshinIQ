"""Models for central Source Registry, source hierarchy tiers, and conflict tracking."""

from enum import Enum, IntEnum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class SourceTier(IntEnum):
    """Source authority hierarchy (Tier 1 is highest authority)."""
    TIER_1_OFFICIAL = 1           # Official HoYoverse, patch notes, in-game client text
    TIER_2_THEORYCRAFTING = 2     # Curated theorycrafting (KQM Guides, KQM TCL)
    TIER_3_STRUCTURED_DATA = 3    # Maintained structured datamined game data (Project Amber, AnimeGameData)
    TIER_4_STATISTICAL = 4        # Aggregated statistical resources (Akasha, YSHelper)
    TIER_4_ESTABLISHED_WIKI = 4   # Selected Genshin Wiki sources (Fandom, etc.)
    TIER_5_COMMUNITY = 5          # Community wikis, forums, Reddit discussions


class SourceType(str, Enum):
    """Source classification types."""
    OFFICIAL = "OFFICIAL"
    KQM = "KQM"
    TCL = "TCL"
    STRUCTURED_DATA = "STRUCTURED_DATA"
    STATISTICAL = "STATISTICAL"
    ESTABLISHED_WIKI = "ESTABLISHED_WIKI"
    COMMUNITY = "COMMUNITY"
    OTHER = "OTHER"
    # Backwards-compatibility aliases
    AUTHORITATIVE = "OFFICIAL"
    THEORYCRAFTING = "KQM"
    WIKI = "ESTABLISHED_WIKI"


class SourceDerivationRelationship(str, Enum):
    """Derivation relationship of a data source to prevent naive majority-vote errors."""
    PRIMARY_ORIGINAL = "PRIMARY_ORIGINAL"    # Direct datamined or original primary source (e.g. AnimeGameData)
    OFFICIAL = "OFFICIAL"                    # First-party authoritative publisher (HoYoverse announcements, client text)
    DERIVED_FROM = "DERIVED_FROM"            # Downstream derivative of another known source (e.g. genshin-db <- AnimeGameData)
    AGGREGATOR = "AGGREGATOR"                # Aggregator / community REST API (Project Amber, genshin.dev)
    REFERENCE = "REFERENCE"                  # Theorycrafting library, catalog, or technical reference (KQM, Honey Hunter, Genshin Optimizer)
    UNKNOWN = "UNKNOWN"                      # Unclassified source


class Source(BaseModel):
    """A canonical source registered in the GenshinIQ ecosystem."""
    source_id: str = Field(..., description="Unique slug identifier (e.g., src_kqm_guides)")
    name: str = Field(..., description="Display name of the source")
    tier: SourceTier = Field(..., description="Authority hierarchy tier (1=Highest)")
    source_type: SourceType = Field(..., description="Classification category")
    base_url: str = Field(..., description="Base retrieval or organization URL")
    canonical_verification_url: str = Field(..., description="User-facing canonical verification URL")
    trust_level: str = Field(..., description="Trust rating descriptor")
    supported_topics: List[str] = Field(default_factory=list, description="Topics this source is approved for")
    update_frequency: str = Field(default="VARIABLE", description="CONTINUOUS, PER_PATCH, DAILY, etc.")
    freshness_policy: str = Field(default="VERSION_ALIGNED", description="Policy for staleness: VERSION_ALIGNED, TIME_DECAY, STATIC")
    retrieval_timeout_seconds: float = Field(default=5.0, description="HTTP timeout for external retrieval")
    enabled: bool = Field(default=True, description="Whether this source is currently active")
    derivation_relationship: SourceDerivationRelationship = Field(
        default=SourceDerivationRelationship.UNKNOWN,
        description="Source independence and derivation relationship"
    )
    parent_source_id: Optional[str] = Field(
        default=None,
        description="ID of the upstream source if this source is DERIVED_FROM"
    )
    derived_from: List[str] = Field(
        default_factory=list,
        description="List of parent source IDs if derived from one or more sources"
    )
    approved_domains: List[str] = Field(
        default_factory=list,
        description="List of knowledge contract domains this source is approved for"
    )
    derivation_notes: Optional[str] = Field(
        default=None,
        description="Details regarding source derivation, upstream dependencies, and corroboration rules"
    )

    def is_derived_from(self, candidate_ancestor_id: str, registry_sources: Optional[Dict[str, "Source"]] = None) -> bool:
        """Check if this source directly or transitively derives from candidate_ancestor_id."""
        ancestors = set(self.derived_from)
        if self.parent_source_id:
            ancestors.add(self.parent_source_id)
        if candidate_ancestor_id in ancestors:
            return True
        if registry_sources:
            for parent_id in list(ancestors):
                parent = registry_sources.get(parent_id)
                if parent and parent.is_derived_from(candidate_ancestor_id, registry_sources):
                    return True
        return False


class SourceRegistryData(BaseModel):
    """Schema for data/canonical/source_registry.json."""
    schema_version: str = "1.0"
    updated_at: str
    sources: List[Source] = Field(default_factory=list)


class ConflictRecord(BaseModel):
    """Represents an auditable claim conflict between two sources."""
    entity_name: str
    topic: str
    source_a: str
    source_b: str
    tier_a: SourceTier
    tier_b: SourceTier
    version_a: str
    version_b: str
    claim_a: str
    claim_b: str
    conflict_status: str = Field(default="UNRESOLVED", description="UNRESOLVED, RESOLVED, SUPERSEDED")
    detected_at: str
    resolution_notes: Optional[str] = None
