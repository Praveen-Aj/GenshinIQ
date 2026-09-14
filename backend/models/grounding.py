"""Phase 10: Citation and Grounding Data Models.

Defines the core models for:
1. Citation Levels: DATASET, SOURCE, CALCULATION, ACCOUNT
2. Claim Support Representation: Claim, Evidence, Evidence Type, Source, Version, Confidence
3. Grounding Verification Results & Scoring
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

from backend.models.query_router import EvidenceType


class CitationType(str, Enum):
    """Four mandatory citation levels defined in Phase 10 architecture."""
    DATASET = "dataset"          # Canonical structured facts (stats, scalings, element, weapon type)
    SOURCE = "source"            # Curated external knowledge (KQM guides, official patch notes, TCL)
    CALCULATION = "calculation"  # Deterministic computations (Stat Engine, CV, weapon deltas)
    ACCOUNT = "account"          # User's imported account data (Enka showcase, GOOD inventory)


class ConfidenceLevel(str, Enum):
    """Confidence classification for claim-evidence verification."""
    HIGH = "high"                # Directly backed by authoritative canonical/calculation evidence
    MEDIUM = "medium"            # Supported by theorycrafting consensus or recent evidence
    LOW = "low"                  # Inferred or qualified with noticeable uncertainty
    UNVERIFIED = "unverified"    # Evidence absent or conflicting


class GroundingStatus(str, Enum):
    """Overall grounding verification status of an assistant response."""
    FULLY_GROUNDED = "fully_grounded"        # >= 85% claims verified, no critical contradictions
    PARTIALLY_GROUNDED = "partially_grounded"  # 50% - 84% claims verified, minor ungrounded statements
    UNGROUNDED = "ungrounded"                # < 50% claims verified or critical hallucination detected


class SupportedClaim(BaseModel):
    """A single factual claim extracted from a response with its backing evidence.

    Internally represents:
    - Claim
    - Evidence
    - Evidence type
    - Source
    - Version
    - Confidence
    """
    claim_text: str = Field(..., description="The factual assertion or proposition from the response")
    evidence_text: str = Field(..., description="The exact evidence passage, field, or value supporting it")
    evidence_type: EvidenceType = Field(..., description="Classification of the supporting evidence")
    source: str = Field(..., description="Source identifier (e.g. Canonical DB, Doc ID, Showcase UID)")
    version: Optional[str] = Field(None, description="Game version associated with the evidence")
    confidence: ConfidenceLevel = Field(default=ConfidenceLevel.HIGH, description="Confidence classification")
    citation_type: CitationType = Field(default=CitationType.SOURCE, description="Citation level")
    verified: bool = Field(default=True, description="Whether claim has been verified against evidence")
    verification_notes: Optional[str] = Field(None, description="Explanation or audit notes")


class GroundingVerificationResult(BaseModel):
    """Result of validating an assistant response against its evidence bundle."""
    status: GroundingStatus = Field(..., description="Overall response grounding status")
    score: float = Field(..., ge=0.0, le=1.0, description="Fraction of claims grounded (0.0 to 1.0)")
    claims: List[SupportedClaim] = Field(default_factory=list, description="Verified claim-evidence pairs")
    unsupported_claims: List[str] = Field(default_factory=list, description="Extracted claims lacking evidence")
    total_claims: int = Field(default=0, description="Total factual claims evaluated")
    grounded_claims: int = Field(default=0, description="Number of verified claims")
    warnings: List[str] = Field(default_factory=list, description="Any potential grounding risks or caveats")
