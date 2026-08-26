"""Data models for curated Genshin knowledge documents and source tracking."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class SourceType(str, Enum):
    """Source classification hierarchy."""
    AUTHORITATIVE = "AUTHORITATIVE"      # Official game data, in-game descriptions, patch notes
    THEORYCRAFTING = "THEORYCRAFTING"    # KQM (KeqingMains), TCL (Theorycrafting Library)
    STATISTICAL = "STATISTICAL"          # Aggregated usage data (Akasha, YShelper)
    COMMUNITY = "COMMUNITY"              # Community guides and discussion


class KnowledgeMetadata(BaseModel):
    """Metadata required for every knowledge document."""
    source: str = Field(..., description="e.g. KeqingMains, HoYoverse Official, Genshin Wiki")
    source_url: str = Field(..., description="Canonical source URL")
    source_type: SourceType = Field(..., description="Source classification")
    character: Optional[str] = Field(default=None, description="Associated character if applicable")
    topic: str = Field(..., description="Topic: Character Guide, Mechanics, Team Building, Patch Notes")
    game_version: str = Field(default="5.0", description="Game version when document was written/verified")
    published_at: str = Field(..., description="ISO publication date")
    updated_at: str = Field(..., description="ISO last updated date")
    tags: List[str] = Field(default_factory=list)


class KnowledgeDocument(BaseModel):
    """Complete curated knowledge article."""
    id: str = Field(..., description="Unique document slug")
    title: str
    metadata: KnowledgeMetadata
    summary: str
    content: str = Field(..., description="Markdown content body")


class KnowledgeSearchResult(BaseModel):
    """Search match result for knowledge retrieval."""
    id: str
    title: str
    source: str
    source_type: SourceType
    character: Optional[str] = None
    topic: str
    game_version: str
    summary: str
    snippet: str
    relevance_score: float = 1.0
