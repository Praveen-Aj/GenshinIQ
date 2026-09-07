"""Pydantic models for Genshin Impact game versioning, patch history, and data staleness."""

from datetime import date
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class GameVersion(BaseModel):
    """Canonical representation of a Genshin Impact game update/patch."""
    version: str = Field(..., description="Semantic version string, e.g. '5.4'")
    name: str = Field(..., description="Official patch name, e.g. 'Dreams of Light Upon the Flowing Star'")
    release_date: str = Field(..., description="ISO release date, YYYY-MM-DD")
    major_region: str = Field(..., description="Primary region associated with the patch, e.g. 'Natlan'")
    is_current: bool = Field(default=False, description="True if this is the active live game version")
    is_upcoming: bool = Field(default=False, description="True if this version is announced/unreleased")
    patch_notes_doc_id: Optional[str] = Field(default=None, description="Linked knowledge document ID for patch notes")


class VersionStatus(BaseModel):
    """Current live game version status and health reporting."""
    current_version: str
    patch_name: str
    release_date: str
    major_region: str
    app_version: str
    total_tracked_versions: int
    latest_canonical_update: str
    stale_document_count: int
    total_document_count: int


class StalenessEvaluation(BaseModel):
    """Result of evaluating a document or entity against current version."""
    entity_version: str
    current_version: str
    is_current: bool
    is_stale: bool
    version_distance: int = Field(..., description="Number of minor patch versions behind current")
    warning: Optional[str] = None
