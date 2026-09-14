"""Pydantic models for Phase 9: Best-Effort Knowledge Escalation.

Defines schemas for:
- Freshness levels (CURRENT, RECENT, STALE, UNKNOWN)
- Escalation triggers (no evidence, stale evidence, explicit request, etc.)
- Escalated evidence items with strict provenance
- Escalation decisions and results
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.models.source_registry import SourceTier, SourceType


class FreshnessLevel(str, Enum):
    """Semantic freshness categorization for retrieved evidence."""
    CURRENT = "CURRENT"      # Confirmed matching the current live game version
    RECENT = "RECENT"        # Recent compatible version; not superseded by major changes
    STALE = "STALE"          # Superseded by subsequent patch changes or obsolete
    UNKNOWN = "UNKNOWN"      # Version/date could not be conclusively determined


class EscalationTrigger(str, Enum):
    """Reason why local knowledge was deemed insufficient, triggering external escalation."""
    NO_LOCAL_EVIDENCE = "NO_LOCAL_EVIDENCE"                    # No local documents or canonical entries exist
    BELOW_QUALITY_THRESHOLD = "BELOW_QUALITY_THRESHOLD"        # Local evidence is low tier or unverified
    STALE_LOCAL_EVIDENCE = "STALE_LOCAL_EVIDENCE"              # Local evidence is from an older, superseded patch
    INSUFFICIENT_RELEVANCE = "INSUFFICIENT_RELEVANCE"          # Local matches score below relevance cutoff
    MISSING_NEW_ENTITY = "MISSING_NEW_ENTITY"                  # Entity released after local data snapshot
    EXPLICIT_CURRENT_REQUEST = "EXPLICIT_CURRENT_REQUEST"      # User explicitly asks for latest/current/new info
    POST_SNAPSHOT_CONTENT = "POST_SNAPSHOT_CONTENT"            # Content known to belong to newer version
    SOURCE_CONFLICT = "SOURCE_CONFLICT"                        # Multiple local sources disagree
    PARTIAL_LOCAL_KB = "PARTIAL_LOCAL_KB"                      # Incomplete coverage for requested entity
    ROUTER_EXTERNAL_REQUIRED = "ROUTER_EXTERNAL_REQUIRED"      # Phase 8 router explicitly flagged external source


class EscalatedEvidenceItem(BaseModel):
    """A single validated evidence item retrieved via external knowledge escalation.
    
    Preserves strict provenance: RETRIEVED != VALIDATED != CURRENT.
    """
    source_name: str = Field(..., description="Display name of the source")
    source_url: str = Field(..., description="URL from which this evidence was retrieved")
    source_tier: SourceTier = Field(..., description="Hierarchy authority tier (1 to 5)")
    source_type: SourceType = Field(..., description="Classification category (OFFICIAL, KQM, etc.)")
    retrieved_at: str = Field(..., description="ISO 8601 UTC timestamp of retrieval")
    published_at: Optional[str] = Field(default=None, description="ISO publication timestamp if available")
    updated_at: Optional[str] = Field(default=None, description="ISO last updated timestamp if available")
    game_version: Optional[str] = Field(default=None, description="Applicable game version (e.g., '7.0')")
    freshness: FreshnessLevel = Field(default=FreshnessLevel.UNKNOWN, description="Semantic freshness assessment")
    relevance: float = Field(default=1.0, ge=0.0, le=1.0, description="Relevance score to query (0.0 to 1.0)")
    retrieval_status: str = Field(
        default="VALIDATED",
        description="SUCCESS, VALIDATED, STALE_REJECTED, IRRELEVANT_REJECTED, TIMEOUT, HTTP_ERROR, PARSE_ERROR"
    )
    content: str = Field(..., description="Normalized evidence content block")
    raw_content: Optional[str] = Field(default=None, description="Original raw excerpt prior to normalization")
    validation_notes: str = Field(default="", description="Auditable reasoning on freshness and validity")


class EscalationDecision(BaseModel):
    """Decision by the quality/freshness evaluator on whether to escalate to external sources."""
    should_escalate: bool = Field(..., description="True if escalation must be attempted")
    trigger: Optional[EscalationTrigger] = Field(default=None, description="Primary trigger for escalation")
    target_query: str = Field(..., description="Search query or entity to query externally")
    required_tier: Optional[SourceTier] = Field(default=None, description="Minimum acceptable authority tier")
    target_version: Optional[str] = Field(default=None, description="Target game version required for freshness")
    reason: str = Field(..., description="Detailed explanation of the escalation decision")


class EscalationResult(BaseModel):
    """Aggregate result of an external knowledge escalation attempt."""
    success: bool = Field(..., description="True if valid, sufficiently fresh evidence was acquired")
    decision: EscalationDecision = Field(..., description="The decision that led to this escalation")
    items: List[EscalatedEvidenceItem] = Field(default_factory=list, description="Validated evidence items acquired")
    sources_attempted: List[str] = Field(default_factory=list, description="Source names/URLs attempted")
    sources_succeeded: List[str] = Field(default_factory=list, description="Source names/URLs that responded successfully")
    sources_failed: List[str] = Field(default_factory=list, description="Source names/URLs that failed or timed out")
    failure_reason: Optional[str] = Field(default=None, description="Why escalation failed or was insufficient")
    is_current_verified: bool = Field(
        default=False,
        description="True ONLY if at least one item was verified as CURRENT for the active game version"
    )
    conflicts_detected: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Preserved conflicts if differing sources returned conflicting claims"
    )
