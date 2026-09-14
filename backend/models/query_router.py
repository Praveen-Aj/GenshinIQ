"""Pydantic models for Phase 8 Query Routing & Tool Orchestration.

Defines intent categories, source requirements, routing decisions,
and evidence tracking structures for the multi-intent query router.
"""

from enum import Enum
from typing import Dict, List, Optional, Set
from pydantic import BaseModel, Field


class QueryIntent(str, Enum):
    """Granular query intent categories for routing decisions."""
    BASIC_GAME_FACT = "BASIC_GAME_FACT"
    CHARACTER_BUILD = "CHARACTER_BUILD"
    ACCOUNT_BUILD_REVIEW = "ACCOUNT_BUILD_REVIEW"
    WEAPON_COMPARISON = "WEAPON_COMPARISON"
    ARTIFACT_ANALYSIS = "ARTIFACT_ANALYSIS"
    STAT_CALCULATION = "STAT_CALCULATION"
    TEAM_BUILDING = "TEAM_BUILDING"
    FARMING = "FARMING"
    VERSION_SENSITIVE = "VERSION_SENSITIVE"
    KNOWLEDGE_SEARCH = "KNOWLEDGE_SEARCH"
    MULTI_SOURCE = "MULTI_SOURCE"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class DataSource(str, Enum):
    """Available data sources and tools for evidence gathering."""
    CANONICAL_GAME_DATA = "CANONICAL_GAME_DATA"
    KNOWLEDGE_BASE = "KNOWLEDGE_BASE"
    ACCOUNT_SHOWCASE = "ACCOUNT_SHOWCASE"
    ACCOUNT_INVENTORY = "ACCOUNT_INVENTORY"
    STAT_ENGINE = "STAT_ENGINE"
    VERSION_SERVICE = "VERSION_SERVICE"
    EXTERNAL_ESCALATION = "EXTERNAL_ESCALATION"
    GEMINI_REASONING = "GEMINI_REASONING"


class EvidenceType(str, Enum):
    """Classification of evidence provenance in the final answer."""
    CANONICAL_GAME_FACT = "CANONICAL_GAME_FACT"
    ACCOUNT_FACT = "ACCOUNT_FACT"
    DETERMINISTIC_CALCULATION = "DETERMINISTIC_CALCULATION"
    THEORYCRAFTING = "THEORYCRAFTING"
    EXTERNAL_EVIDENCE = "EXTERNAL_EVIDENCE"
    AI_EXPLANATION = "AI_EXPLANATION"
    VERSION_CONTEXT = "VERSION_CONTEXT"


class DetectedEntity(BaseModel):
    """An entity (character, weapon, artifact set, material) detected in the query."""
    entity_type: str = Field(..., description="character, weapon, artifact_set, or material")
    name: str = Field(..., description="Canonical entity name")
    matched_text: str = Field("", description="The text fragment that matched")


class RoutingDecision(BaseModel):
    """The routing decision produced by the query router."""
    primary_intent: QueryIntent = Field(..., description="Primary classified intent")
    secondary_intents: List[QueryIntent] = Field(default_factory=list, description="Additional applicable intents")
    required_sources: List[DataSource] = Field(default_factory=list, description="Sources that MUST be consulted")
    optional_sources: List[DataSource] = Field(default_factory=list, description="Sources that MAY improve the answer")
    detected_entities: List[DetectedEntity] = Field(default_factory=list, description="Entities found in query")
    requires_account_data: bool = Field(False, description="Whether account/inventory data is needed")
    requires_stat_engine: bool = Field(False, description="Whether deterministic calculations are needed")
    requires_version_check: bool = Field(False, description="Whether version-sensitive filtering is needed")
    reasoning: str = Field("", description="Brief explanation of why this routing was chosen")

    @property
    def all_intents(self) -> List[QueryIntent]:
        """All intents (primary + secondary) in priority order."""
        return [self.primary_intent] + self.secondary_intents


class EvidenceItem(BaseModel):
    """A single piece of evidence gathered from a data source."""
    source: DataSource = Field(..., description="Which source produced this evidence")
    evidence_type: EvidenceType = Field(..., description="Classification of this evidence")
    content: str = Field(..., description="The evidence content block")
    entity_name: Optional[str] = Field(None, description="Related entity name if applicable")
    is_stale: bool = Field(False, description="Whether this evidence has staleness warnings")
    staleness_note: str = Field("", description="Staleness warning detail if applicable")
    game_version: Optional[str] = Field(None, description="Game version of the evidence")


class EvidenceBundle(BaseModel):
    """Complete evidence bundle assembled from all required sources."""
    items: List[EvidenceItem] = Field(default_factory=list, description="All gathered evidence items")
    sources_consulted: List[DataSource] = Field(default_factory=list, description="Sources actually consulted")
    sources_unavailable: List[DataSource] = Field(default_factory=list, description="Required sources that were unavailable")
    is_sufficient: bool = Field(True, description="Whether evidence meets minimum requirements")
    insufficiency_reason: str = Field("", description="Why evidence is insufficient if applicable")
    stat_engine_results: Optional[Dict] = Field(None, description="Raw stat engine output if calculations were run")

    @property
    def evidence_types_used(self) -> List[str]:
        """Unique evidence types present in the bundle."""
        return list(set(item.evidence_type.value for item in self.items))
