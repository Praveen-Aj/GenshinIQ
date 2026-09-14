"""Data models for chat messages, requests, and grounded responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str = Field(..., description="user or model")
    content: str = Field(..., description="The markdown text content of the message")


class ChatRequest(BaseModel):
    """Payload to request assistant generation."""
    messages: List[ChatMessage] = Field(..., description="History of chat messages")
    uid: Optional[str] = Field(None, description="Active Genshin Impact UID")


class Citation(BaseModel):
    """Source citation context for grounded facts, calculations, and account records."""
    source_name: str = Field(..., description="E.g., Canonical Game Database, Enka.Network, KeqingMains")
    source_url: str = Field(..., description="Retrieval source URL or canonical path")
    snippet: str = Field(..., description="Matching text context snippet or calculated value")
    character: Optional[str] = None
    topic: Optional[str] = None
    game_version: Optional[str] = None
    # Phase 3 provenance extensions
    document_id: Optional[str] = Field(None, description="Source document ID slug")
    source_id: Optional[str] = Field(None, description="Canonical source ID (e.g., src_kqm_guides)")
    canonical_url: Optional[str] = Field(None, description="User-facing canonical verification URL")
    source_type: Optional[str] = Field(None, description="Source type classification")
    authority_tier: Optional[int] = Field(None, description="Hierarchy tier (1=Official, 5=Community)")
    content_hash: Optional[str] = Field(None, description="SHA-256 hash of cited document")
    # Phase 10: Citation level and grounding extensions
    citation_type: str = Field(default="source", description="dataset, source, calculation, or account")
    confidence: str = Field(default="high", description="high, medium, low, or unverified")
    claim_supported: Optional[str] = Field(None, description="Specific claim or proposition verified by this citation")
    display_label: Optional[str] = Field(None, description="Consumer-friendly display label (e.g. Canonical Data, Account Showcase)")


class ChatResponse(BaseModel):
    """Response payload containing generated message, classification intent, and citations."""
    content: str = Field(..., description="Grounded response text")
    intent: str = Field(..., description="Legacy intent field (general or account)")
    citations: List[Citation] = Field(default_factory=list, description="Retrieve source references")
    # Phase 8: Routing transparency
    query_intents: List[str] = Field(default_factory=list, description="Classified query intent categories")
    sources_used: List[str] = Field(default_factory=list, description="Data sources consulted for this response")
    evidence_types: List[str] = Field(default_factory=list, description="Types of evidence in the response")
    # Phase 10: Grounding status and verified claims
    grounding_status: Optional[str] = Field(default="fully_grounded", description="fully_grounded, partially_grounded, ungrounded")
    grounding_score: Optional[float] = Field(default=1.0, description="Fraction of claims grounded (0.0 - 1.0)")
    claims: List[dict] = Field(default_factory=list, description="Structured claim-evidence pairs backing this response")

