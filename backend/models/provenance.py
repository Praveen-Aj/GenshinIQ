"""Models for dataset provenance and version tracking."""

from typing import Dict, List
from pydantic import BaseModel, Field


class DatasetFileProvenance(BaseModel):
    """Provenance details for a single dataset file."""
    file_name: str
    record_count: int = Field(..., ge=0)
    sha256: str
    updated_at: str
    source_id: str = "src_animegamedata"
    source_url: str = "https://github.com/Dimbreath/AnimeGameData/tree/master/ExcelBinOutput"
    source_version: str = "5.4"
    dataset_version: str = "5.4"
    project_target_version: str = "7.0"
    verification_state: str = "VERIFIED_STRUCTURED"
    verification_status: str = "VERIFIED_STRUCTURED"
    invariance_classification: str = "VERSION_INVARIANT"


class GameDataProvenance(BaseModel):
    """Provenance summary for canonical structured game data."""
    directory: str
    aggregate_sha256: str
    dataset_version: str = "5.4"
    project_target_version: str = "7.0"
    verification_state: str = "VERIFIED_STRUCTURED"
    files: List[DatasetFileProvenance] = Field(default_factory=list)
    characters: int = 0
    weapons: int = 0
    artifact_sets: int = 0
    materials: int = 0


class KnowledgeProvenance(BaseModel):
    """Provenance summary for curated knowledge documents."""
    directory: str
    aggregate_sha256: str
    total_documents: int
    source_type_counts: Dict[str, int] = Field(default_factory=dict)
    source_tier_counts: Dict[str, int] = Field(default_factory=dict)
    source_id_counts: Dict[str, int] = Field(default_factory=dict)
    source_counts: Dict[str, int] = Field(default_factory=dict)
    game_version_counts: Dict[str, int] = Field(default_factory=dict)


class DataProvenanceManifest(BaseModel):
    """Top-level provenance snapshot for the local repository data."""
    schema_version: str = "1.0"
    generated_at: str
    app_version: str
    runtime_cache_dir: str
    game_data: GameDataProvenance
    knowledge_base: KnowledgeProvenance
