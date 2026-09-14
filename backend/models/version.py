"""Pydantic models for Genshin Impact game versioning, patch history, and data staleness."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationStatus(str, Enum):
    """Source verification status of a game version release."""
    VERIFIED_OFFICIAL = "VERIFIED_OFFICIAL"
    VERIFIED_STRUCTURED = "VERIFIED_STRUCTURED"
    CACHED_OFFLINE = "CACHED_OFFLINE"
    UNVERIFIED = "UNVERIFIED"


class FreshnessStatus(str, Enum):
    """Semantic freshness status of knowledge or game data relative to game version."""
    CURRENT = "current"
    RECENT_COMPATIBLE = "recent_compatible"
    STALE = "stale"
    HISTORICAL = "historical"
    UNKNOWN = "unknown"


class GameVersion(BaseModel):
    """Canonical representation of a Genshin Impact game update/patch release."""
    version: str = Field(..., description="Semantic version string, e.g. '7.0'")
    name: str = Field(..., description="Official patch name, e.g. 'The Stars Turn Anew'")
    release_date: str = Field(..., description="ISO release date, YYYY-MM-DD")
    end_date: Optional[str] = Field(default=None, description="ISO patch end date if known")
    major_region: str = Field(..., description="Primary region associated with the patch")
    is_released: bool = Field(default=True, description="True if version has been officially released")
    is_upcoming: bool = Field(default=False, description="True if version is unreleased / upcoming")
    is_current: bool = Field(default=False, description="True if this is the active live released game version")
    is_project_target: bool = Field(default=False, description="True if this version serves as project target anchor")
    verification_status: str = Field(default=VerificationStatus.VERIFIED_OFFICIAL.value, description="Verification state of this version record")
    source_id: str = Field(default="src_hoyoverse_patch_notes", description="Registered source ID validating this release")
    source_url: Optional[str] = Field(default="https://genshin.hoyoverse.com/en/news", description="URL where version was verified")
    canonical_url: Optional[str] = Field(default="https://genshin.hoyoverse.com/en/news", description="Canonical news URL")
    retrieved_at: Optional[str] = Field(default="2026-09-08T00:00:00Z", description="When this version was verified")
    patch_notes_doc_id: Optional[str] = Field(default=None, description="Linked knowledge document ID for patch notes")


class VersionStatus(BaseModel):
    """Current live game version status and health reporting."""
    current_version: str = Field(..., description="Actual verified current released game version")
    latest_known_version: str = Field(default="7.0", description="Highest verified version known to GenshinIQ")
    project_target_version: Optional[str] = Field(default=None, description="Project development target anchor if applicable")
    patch_name: str
    release_date: str
    major_region: str
    verification_status: str = Field(default=VerificationStatus.VERIFIED_OFFICIAL.value, description="Verification status of current version")
    discovery_status: str = Field(default="AVAILABLE", description="AVAILABLE or UNAVAILABLE / CACHED_OFFLINE")
    last_version_verification: str = Field(default="2026-09-08T00:00:00Z", description="ISO timestamp of last discovery check")
    app_version: str
    total_tracked_versions: int
    latest_canonical_update: str
    stale_document_count: int
    total_document_count: int
    update_available: bool = Field(default=False, description="True if a newer verified released version was discovered")


class DiscoveredVersionCandidate(BaseModel):
    """A candidate game version discovered from an approved authoritative source."""
    version: str = Field(..., description="Parsed semantic version, e.g. '7.1'")
    name: str = Field(..., description="Official patch name or title")
    release_date: str = Field(..., description="ISO release date, YYYY-MM-DD")
    is_released: bool = Field(default=True, description="True if officially confirmed as already released/live")
    is_upcoming: bool = Field(default=False, description="True if only announced as upcoming/preview")
    source_id: str = Field(default="src_hoyoverse_patch_notes", description="Approved source ID that provided this evidence")
    source_url: str = Field(..., description="Direct verification URL")
    raw_evidence: Optional[str] = Field(default=None, description="Snippet or text evidence confirming status")
    changed_systems: List[str] = Field(default_factory=list, description="Known modified systems/characters if present in patch notes")


class VerificationResult(BaseModel):
    """Result of validating a discovered version candidate against authoritative rules."""
    is_valid: bool = Field(..., description="True if candidate is legitimate and approved for promotion")
    status: str = Field(..., description="PASS, REJECTED_UNRELEASED, REJECTED_FUTURE, FAILED_MALFORMED, ALREADY_CURRENT")
    reason: str = Field(..., description="Human-readable explanation of verification outcome")
    candidate: Optional[DiscoveredVersionCandidate] = None


class VersionCheckResult(BaseModel):
    """Result of an end-to-end DISCOVER -> VERIFY -> PROMOTE check."""
    current_version: str = Field(..., description="Current active registry version before check")
    discovered_version: Optional[str] = Field(default=None, description="Discovered version string if any")
    verification_status: str = Field(..., description="Verification outcome string")
    update_available: bool = Field(default=False, description="True if newer released version exists")
    promoted: bool = Field(default=False, description="True if candidate was promoted into canonical registry")
    discovery_status: str = Field(default="AVAILABLE", description="AVAILABLE, CACHED_OFFLINE, MALFORMED_DATA")
    effective_current_version: str = Field(..., description="Active current version after check/promotion")
    message: str = Field(..., description="Summary of check outcome")


class StalenessEvaluation(BaseModel):
    """Result of evaluating a document or entity against current version."""
    entity_version: str
    current_version: str
    freshness_status: FreshnessStatus = Field(default=FreshnessStatus.CURRENT, description="Semantic freshness status")
    is_current: bool
    is_stale: bool
    version_distance: int = Field(..., description="Number of minor patch versions behind current")
    warning: Optional[str] = None
    affected_systems: List[str] = Field(default_factory=list, description="Scopes this evaluation checked")


class DatasetVersionState(BaseModel):
    """
    Decoupled version state tracking across detection, availability, verification, and canonical status.
    Guarantees that a higher detected game version (e.g. 8.0) does not falsely relabel an earlier dataset (e.g. 5.4).
    """
    detected_game_version: str = Field(..., description="Live version announced by HoYoverse official")
    latest_known_game_version: str = Field(..., description="Highest verified released patch in version registry")
    latest_available_dataset_version: str = Field(..., description="Highest available version detected from AnimeGameData")
    latest_verified_dataset_version: str = Field(..., description="Highest dataset version that passed all validation gates")
    active_canonical_dataset_version: str = Field(..., description="Active canonical dataset currently driving calculations")
    latest_knowledge_version: str = Field(default="5.0", description="Highest version covered in knowledge base")
    latest_verified_knowledge_version: str = Field(default="5.0", description="Highest knowledge version passing completeness audit")
    version_completeness_status: str = Field(default="INCOMPLETE", description="Overall completeness status (COMPLETE, INCOMPLETE, BLOCKED, UNKNOWN)")
    project_target_version: str = Field(..., description="Project development target anchor (e.g. 7.0)")
    update_status: str = Field(default="Up to date", description="Human-readable status of version synchronization")
    last_successful_refresh: Optional[str] = None
    last_failed_refresh: Optional[str] = None
    failure_reason: Optional[str] = None


class CompletenessStatus(str, Enum):
    """Status classification for multi-domain version completeness."""
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    INCOMPLETE = "INCOMPLETE"
    STALE = "STALE"
    UNKNOWN = "UNKNOWN"
    MISSING = "MISSING"
    UNVERIFIED = "UNVERIFIED"
    CONFLICT = "CONFLICT"
    BLOCKED = "BLOCKED"


class EntityCoverageMetrics(BaseModel):
    """Entity-level coverage metrics for a specific information category."""
    category: str = Field(..., description="Category name (e.g. 'characters', 'quests')")
    expected_count: int = Field(default=0, description="Expected total entities for target version")
    found_count: int = Field(default=0, description="Entities found in storage")
    verified_count: int = Field(default=0, description="Entities passing verification and non-empty")
    missing_count: int = Field(default=0, description="Entities missing from dataset/knowledge")
    stale_count: int = Field(default=0, description="Entities flagged stale or pre-target")
    unverified_count: int = Field(default=0, description="Entities lacking verified source provenance")
    coverage_ratio: float = Field(default=0.0, description="Ratio of verified_count / expected_count (0.0 to 1.0)")
    status: CompletenessStatus = Field(default=CompletenessStatus.INCOMPLETE)
    sample_missing: List[str] = Field(default_factory=list, description="Sample of missing entity names/IDs")


class StructuredDataCompleteness(BaseModel):
    """Structured canonical numerical game data coverage."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    coverage: float = 0.0
    characters: EntityCoverageMetrics
    weapons: EntityCoverageMetrics
    artifacts: EntityCoverageMetrics
    materials: EntityCoverageMetrics
    curves: EntityCoverageMetrics
    domains: EntityCoverageMetrics
    relationships: EntityCoverageMetrics


class GameContentCompleteness(BaseModel):
    """Game-world content, quest, enemy, and system coverage."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    coverage: float = 0.0
    quests: EntityCoverageMetrics
    events: EntityCoverageMetrics
    domains: EntityCoverageMetrics
    enemies: EntityCoverageMetrics
    regions: EntityCoverageMetrics
    achievements: EntityCoverageMetrics
    crafting: EntityCoverageMetrics
    farming: EntityCoverageMetrics
    mechanics: EntityCoverageMetrics


class KnowledgeCompleteness(BaseModel):
    """Curated knowledge base, guide, theorycrafting, and mechanics coverage."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    coverage: float = 0.0
    character_guides: EntityCoverageMetrics
    weapon_guides: EntityCoverageMetrics
    artifact_guides: EntityCoverageMetrics
    team_building: EntityCoverageMetrics
    mechanics: EntityCoverageMetrics
    theorycrafting: EntityCoverageMetrics
    farming: EntityCoverageMetrics
    current_version_changes: EntityCoverageMetrics


class ProvenanceCompleteness(BaseModel):
    """Provenance integrity coverage across all stored records."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    records_with_valid_provenance: int = 0
    records_missing_provenance: int = 0
    records_with_stale_provenance: int = 0
    records_with_unverifiable_source: int = 0
    all_required_sources_verified: bool = False


class FreshnessCompleteness(BaseModel):
    """Freshness evaluation of data and knowledge against target version."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    current_records: int = 0
    compatible_records: int = 0
    stale_records: int = 0
    unknown_records: int = 0
    freshness_ratio: float = 0.0


class VersionDeltaCompleteness(BaseModel):
    """Coverage of new entities and changes introduced in target version."""
    status: CompletenessStatus = CompletenessStatus.INCOMPLETE
    base_version: str = "5.4"
    target_version: str = "7.0"
    new_characters_count: int = 0
    new_weapons_count: int = 0
    new_artifacts_count: int = 0
    new_content_count: int = 0
    covered_new_entities_count: int = 0
    missing_new_entities: List[str] = Field(default_factory=list)


class VersionCompletenessReport(BaseModel):
    """Comprehensive version completeness release gate report."""
    live_version: str
    dataset_version: str
    knowledge_version: str
    active_canonical_version: str
    project_target_version: str
    overall_status: CompletenessStatus
    phase_8_allowed: bool = False
    live_characters_count: int = 95
    unreleased_characters_count: int = 24
    canonical_data_completeness: float = 1.0
    mechanics_completeness: float = 1.0
    expert_guide_coverage: float = 0.9474
    unreleased_entities_excluded: int = 24
    structured_data: StructuredDataCompleteness
    game_content: GameContentCompleteness
    knowledge: KnowledgeCompleteness
    provenance: ProvenanceCompleteness
    freshness: FreshnessCompleteness
    version_delta: VersionDeltaCompleteness
    blockers: List[str] = Field(default_factory=list)
    last_audit_time: str


class PhaseGateResponse(BaseModel):
    """Hard phase gate response controlling Phase 8 readiness."""
    phase_8_allowed: bool = False
    reason: str
    blocking_categories: List[str] = Field(default_factory=list)
    version_completeness_status: str
    active_canonical_version: str
    live_version: str
    audit_time: str



class UpstreamDiscoveryResult(BaseModel):
    """Result of discovering upstream dataset availability from primary/secondary sources."""
    source_id: str = "src_animegamedata"
    repository_url: str = "https://github.com/DimbreathBot/AnimeGameData"
    discovered_version: str
    commit_sha: Optional[str] = None
    commit_message: Optional[str] = None
    discovery_timestamp: str
    is_newer_than_active: bool = False
    is_newer_than_verified: bool = False
    raw_files_available: List[str] = Field(default_factory=list)


class VersionDiffItem(BaseModel):
    """A single entity-level or curve-level difference between two dataset versions."""
    entity_type: str = Field(..., description="'character', 'weapon', 'artifact', 'material', 'curve'")
    entity_id: str
    entity_name: str
    change_type: str = Field(..., description="'ADDED', 'REMOVED', 'MODIFIED'")
    field_changes: Dict[str, Any] = Field(default_factory=dict, description="Field-level before/after diffs")
    provenance_source: str = "src_animegamedata"


class VersionDiffReport(BaseModel):
    """Deterministic diff comparison report between base and target dataset versions."""
    base_version: str
    target_version: str
    timestamp: str
    total_changes: int = 0
    added_count: int = 0
    modified_count: int = 0
    removed_count: int = 0
    items: List[VersionDiffItem] = Field(default_factory=list)



class CrossSourceValidationStatus(str, Enum):
    """Derivation-aware comparison classification between primary and secondary sources."""
    AGREEMENT = "AGREEMENT"                    # Independent sources match exactly
    DERIVED_AGREEMENT = "DERIVED_AGREEMENT"    # Agreement with a source derived from primary (corroboration only)
    PRIMARY_ONLY = "PRIMARY_ONLY"              # Entity/field exists solely in primary source
    SECONDARY_ONLY = "SECONDARY_ONLY"          # Entity/field exists solely in secondary source
    CONFLICT = "CONFLICT"                      # Discrepancy between sources on critical or non-critical fields


class CrossSourceFieldComparison(BaseModel):
    """Field-level cross-source audit comparison."""
    entity_type: str = Field(..., description="'character', 'weapon', 'artifact', 'material'")
    entity_id: str
    entity_name: str
    field_name: str
    primary_source_id: str = "src_animegamedata"
    primary_value: Any
    secondary_source_id: str
    secondary_value: Any
    status: CrossSourceValidationStatus
    is_critical_numerical_field: bool = Field(default=False, description="True if discrepancy directly alters stat scaling")
    notes: Optional[str] = None


class CrossSourceValidationReport(BaseModel):
    """Full cross-source verification report across secondary and derived catalogs."""
    version: str
    timestamp: str
    total_compared_entities: int = 0
    agreement_count: int = 0
    derived_agreement_count: int = 0
    primary_only_count: int = 0
    secondary_only_count: int = 0
    conflict_count: int = 0
    critical_conflict_count: int = 0
    is_promotable: bool = Field(default=True, description="False if any critical numerical field has a CONFLICT")
    blocking_conflicts: List[CrossSourceFieldComparison] = Field(default_factory=list)
    comparisons: List[CrossSourceFieldComparison] = Field(default_factory=list)


class DatasetVersionManifest(BaseModel):
    """Cryptographic and audit manifest stored immutably inside each versioned dataset folder."""
    source_id: str = Field(..., description="Registered source ID that produced this raw or processed dataset")
    source_url: str = Field(..., description="Repository or endpoint URL")
    source_version: str = Field(..., description="Upstream source version tag")
    dataset_version: str = Field(..., description="Engine dataset version, e.g. '5.4'")
    retrieved_at: str = Field(..., description="ISO timestamp of acquisition")
    content_hash: str = Field(..., description="Aggregate SHA-256 digest of versioned payload")
    schema_version: str = Field(default="1.0")
    record_counts: Dict[str, int] = Field(default_factory=dict, description="Counts by entity category")
    validation_status: str = Field(default="PASSED", description="PASSED, FAILED_SCHEMA, FAILED_CONFLICT, FAILED_NUMERICAL")
    verification_status: str = Field(default="VERIFIED_STRUCTURED", description="VERIFIED_STRUCTURED, UNVERIFIED, REJECTED")
    file_hashes: Dict[str, str] = Field(default_factory=dict, description="SHA-256 digest for each individual file")
