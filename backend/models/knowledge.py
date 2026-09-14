"""Data models for curated Genshin knowledge documents and source tracking."""

import hashlib
from typing import List, Optional
from pydantic import BaseModel, Field, model_validator

from backend.models.source_registry import SourceTier, SourceType


from enum import Enum


class KnowledgeQualityState(str, Enum):
    """Explicit knowledge quality states per GenshinIQ Knowledge Contract."""
    VERIFIED = "VERIFIED"
    VERIFIED_DERIVED = "VERIFIED_DERIVED"
    CURRENT = "CURRENT"
    RECENT_COMPATIBLE = "RECENT_COMPATIBLE"
    HISTORICAL = "HISTORICAL"
    STALE = "STALE"
    PARTIAL = "PARTIAL"
    UNKNOWN = "UNKNOWN"
    CONFLICT = "CONFLICT"
    UNVERIFIED = "UNVERIFIED"


class EvidenceClassification(str, Enum):
    """Rigorous evidence classification for combat rules and game mechanics."""
    OFFICIALLY_DOCUMENTED = "OFFICIALLY_DOCUMENTED"
    EXPERT_TESTED = "EXPERT_TESTED"
    DERIVED_CALCULATED = "DERIVED_CALCULATED"
    COMMUNITY_INTERPRETATION = "COMMUNITY_INTERPRETATION"
    UNKNOWN = "UNKNOWN"


def compute_content_hash(content: str) -> str:
    """Compute deterministic SHA-256 hash of normalized markdown document content."""
    normalized = content.strip().replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class KnowledgeMetadata(BaseModel):
    """Structured provenance and classification metadata required for every knowledge document."""
    source_id: str = Field(..., description="Canonical source registry ID (e.g., src_kqm_guides)")
    source: str = Field(..., description="Human-readable source provider name")
    source_url: str = Field(..., description="Retrieval endpoint / URL where content was fetched")
    canonical_url: str = Field(..., description="Canonical user-facing verification URL")
    source_type: SourceType = Field(..., description="Source classification type")
    authority_tier: SourceTier = Field(..., description="Authority hierarchy tier (1=Highest, 5=Lowest)")
    character: Optional[str] = Field(default=None, description="Associated character if applicable")
    topic: str = Field(..., description="Topic: Character Guide, Game Mechanics, Team Building, Patch Notes")
    game_version: str = Field(default="7.0", description="Game version when document was written/verified")
    published_at: Optional[str] = Field(default=None, description="ISO publication date, or null if unknown")
    updated_at: Optional[str] = Field(default=None, description="ISO last updated date, or null if unknown")
    retrieved_at: str = Field(..., description="ISO timestamp when GenshinIQ retrieved/normalized this content")
    content_hash: str = Field(..., description="SHA-256 digest of normalized markdown body")
    freshness_status: Optional[str] = Field(default=None, description="current, recent_compatible, stale, historical, or unknown")
    quality_state: Optional[KnowledgeQualityState] = Field(default=KnowledgeQualityState.VERIFIED, description="Explicit contractual quality state")
    evidence_classification: Optional[EvidenceClassification] = Field(default=None, description="Classification of underlying evidence")
    affected_systems: List[str] = Field(default_factory=list, description="Scopes this document depends on (character, weapon, mechanic)")
    last_verified: Optional[str] = Field(default=None, description="ISO timestamp when document was last verified against authoritative source")
    tags: List[str] = Field(default_factory=list, description="Searchable keyword tags")

    @model_validator(mode="after")
    def validate_against_source_registry(self):
        from backend.services.source_registry_service import source_registry_service
        src = source_registry_service.get_source(self.source_id)
        if not src:
            raise ValueError(f"Unregistered source_id: '{self.source_id}'. Must be defined in source_registry.json")
        if self.authority_tier != src.tier:
            raise ValueError(
                f"Tier mismatch for {self.source_id}: registered={src.tier}, claimed={self.authority_tier}"
            )
        return self


class KnowledgeDocument(BaseModel):
    """Complete curated knowledge article with structured provenance."""
    id: str = Field(..., description="Unique document slug identifier")
    title: str = Field(..., description="Article title")
    metadata: KnowledgeMetadata
    summary: str = Field(..., description="Executive summary")
    content: str = Field(..., description="Markdown content body")

    def verify_hash(self) -> bool:
        """Verify that the recorded content_hash matches the actual content body."""
        return self.metadata.content_hash == compute_content_hash(self.content)


class KnowledgeSearchResult(BaseModel):
    """Search match result for knowledge retrieval with provenance references."""
    id: str
    title: str
    source_id: str
    source: str
    canonical_url: str
    source_type: SourceType
    authority_tier: SourceTier
    character: Optional[str] = None
    topic: str
    game_version: str
    summary: str
    snippet: str
    content_hash: str
    relevance_score: float = 1.0
    chunk_id: Optional[str] = None
    section_heading: Optional[str] = None


class SemanticChunk(BaseModel):
    """Meaningful semantic section of a knowledge document preserving context and provenance."""
    chunk_id: str = Field(..., description="Unique chunk slug identifier, e.g. 'kqm_kazuha_guide#weapon-rankings'")
    document_id: str = Field(..., description="Parent document identifier")
    title: str = Field(..., description="Parent document title")
    section_heading: str = Field(..., description="Section heading hierarchy, e.g. 'Overview > Core Mechanics'")
    content: str = Field(..., description="Markdown chunk content (tables, formulas, descriptions)")
    character: Optional[str] = Field(default=None, description="Associated character if applicable")
    topic: str = Field(..., description="Topic of the document")
    game_version: str = Field(default="7.0", description="Game version when document was written/verified")
    freshness_status: str = Field(default="current", description="current, recent_compatible, stale, historical, or unknown")
    affected_systems: List[str] = Field(default_factory=list, description="Scopes this chunk depends on")
    source_id: str = Field(..., description="Registered canonical source ID")
    source: str = Field(..., description="Source name")
    source_url: str = Field(..., description="Direct retrieval URL")
    canonical_url: str = Field(..., description="Canonical verification URL")
    authority_tier: SourceTier = Field(..., description="Authority hierarchy tier (1 to 5)")
    source_type: SourceType = Field(..., description="Source classification type")
    content_hash: str = Field(..., description="Parent document content hash")
    chunk_index: int = Field(default=0, description="Sequential chunk index in document")
    token_count: int = Field(default=0, description="Approximate token count of chunk content")


class QuerySignals(BaseModel):
    """Signals extracted from a user search/RAG query."""
    query: str
    detected_characters: List[str] = Field(default_factory=list)
    detected_weapons: List[str] = Field(default_factory=list)
    detected_artifacts: List[str] = Field(default_factory=list)
    detected_mechanics: List[str] = Field(default_factory=list)
    retrieval_mode: str = Field(default="general", description="factual, mechanics, character, weapon, artifact, guide, farming, historical, general")
    is_historical_query: bool = Field(default=False, description="True if query explicitly asks about past versions/history")


class RetrievedEvidence(BaseModel):
    """Ranked evidence item returned by the retrieval engine with full provenance."""
    chunk_id: str
    document_id: str
    title: str
    section_heading: str
    content: str
    source_id: str
    source: str
    source_url: str
    canonical_url: str
    source_type: SourceType
    authority_tier: SourceTier
    character: Optional[str] = None
    topic: str
    game_version: str
    freshness_status: str
    affected_systems: List[str] = Field(default_factory=list)
    content_hash: str
    lexical_score: float = Field(default=0.0, description="Normalized BM25 score")
    semantic_score: float = Field(default=0.0, description="Normalized dense vector similarity score")
    composite_score: float = Field(default=0.0, description="Combined final ranking score")
    retrieval_method: str = Field(default="hybrid", description="hybrid, bm25_only, vector_only")
    rank: int = Field(default=1, description="Final rank position in evidence bundle")


class EvidenceBundle(BaseModel):
    """Structured evidence bundle for downstream consumption by Chat and tools."""
    query: str
    signals: QuerySignals
    items: List[RetrievedEvidence] = Field(default_factory=list)
    total_candidates_examined: int = 0
    latency_ms: float = 0.0
    retrieval_status: str = Field(default="OK", description="OK, VECTOR_DEGRADED, LEXICAL_DEGRADED, EMPTY")
    embedding_model: str = Field(default="local-subword-dense-v1")

