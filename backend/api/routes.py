"""API routes for GenshinIQ."""

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from backend.config import settings
from backend.api.auth import require_admin_auth
from backend.services.account_service import account_service
from backend.services.account_inventory_service import (
    account_inventory_service,
    AccountInventoryException,
)
from backend.services.game_data_service import game_data_service
from backend.models.account import (
    AccountArtifactInstance,
    AccountCharacterInstance,
    AccountDiff,
    AccountMaterialInstance,
    AccountSnapshot,
    AccountSummary,
    AccountWeaponInstance,
    CharacterBuild,
    EnkaShowcaseResponse,
    ResolutionStatus,
)
from backend.models.game_data import (
    CharacterData,
    WeaponData,
    ArtifactSetData,
    MaterialData,
    SearchResult,
)
from backend.models.provenance import DataProvenanceManifest
from backend.models.knowledge import (
    EvidenceBundle,
    KnowledgeDocument,
    KnowledgeSearchResult,
    SourceType,
)
from backend.services.knowledge_service import knowledge_service
from backend.services.retrieval_service import retrieval_service
from backend.services.provenance_service import provenance_service
from backend.models.chat import ChatRequest, ChatResponse
from backend.services.rag_service import rag_service
from backend.models.version import (
    GameVersion,
    VersionStatus,
    StalenessEvaluation,
    DatasetVersionState,
    VersionCompletenessReport,
    PhaseGateResponse,
)
from backend.services.version_service import version_service
from backend.services.canonical_data_pipeline import canonical_data_pipeline
from backend.services.version_completeness_gate import version_completeness_gate
from backend.services.knowledge_contract_service import knowledge_contract_service
from backend.services.update_orchestrator import update_orchestrator
from backend.services.version_delta_service import version_delta_service
from backend.models.source_registry import Source, SourceTier
from backend.services.source_registry_service import source_registry_service
from backend.models.stat_engine import (
    CalculationStatus,
    CharacterBuildSnapshot,
    CalculatedCombatStats,
    FullStatBreakdown,
    BuildComparison,
    CustomBuildRequest,
)
from backend.services.stat_engine import stat_engine_service
from backend.services.account_inventory_service import account_inventory_service

router = APIRouter()


# System Diagnostics
@router.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint to verify backend system status and active game version."""
    curr_v = version_service.get_current_version()
    active_canonical = canonical_data_pipeline.get_active_version()
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "version": settings.APP_VERSION,
        "game_version": curr_v.version,
        "active_canonical_dataset_version": active_canonical,
        "game_patch_name": curr_v.name,
        "environment": settings.APP_ENV,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gemini_configured": bool(settings.GEMINI_API_KEY),
        "enka_api_base": settings.ENKA_API_BASE_URL,
    }


# Phase 2: Game Version & Patch History Endpoints
@router.get(
    "/version/current",
    response_model=GameVersion,
    summary="Get Current Live Game Version"
)
def get_current_game_version():
    """Retrieve verified active live game version details."""
    return version_service.get_current_version()


@router.get(
    "/version/history",
    response_model=List[GameVersion],
    summary="List Tracked Game Version History"
)
def list_game_version_history():
    """Retrieve full chronological registry of game versions."""
    return version_service.list_versions()


@router.get(
    "/version/status",
    response_model=VersionStatus,
    summary="Unified Version & Staleness Status"
)
def get_version_status():
    """Get system health, active patch status, and document staleness metrics."""
    stale_docs = knowledge_service.get_stale_documents()
    total_docs = len(knowledge_service.documents)
    return version_service.get_status(
        total_documents=total_docs,
        stale_documents=len(stale_docs),
    )


@router.get(
    "/knowledge/stale",
    summary="List Stale Knowledge Documents"
)
def list_stale_knowledge(
    threshold: int = Query(default=4, description="Patches behind current to consider stale")
):
    """List knowledge documents that are stale relative to the active game version."""
    return knowledge_service.get_stale_documents(stale_threshold_patches=threshold)


# ==============================================================================
# Phase 6: Full Account Inventory Endpoints (GOOD v3)
# ==============================================================================

@router.get(
    "/account",
    response_model=AccountSnapshot,
    summary="Get Full Normalized Account Snapshot"
)
def get_full_account_snapshot():
    """Retrieve the active full normalized account inventory snapshot."""
    snapshot = account_inventory_service.get_active_snapshot()
    if not snapshot:
        raise HTTPException(
            status_code=404,
            detail="No account inventory snapshot imported yet."
        )
    return snapshot


@router.get(
    "/account/summary",
    response_model=AccountSummary,
    summary="Get Account Inventory Summary"
)
def get_account_inventory_summary():
    """Retrieve deterministic account inventory summary metrics."""
    return account_inventory_service.get_summary()


@router.get(
    "/account/characters",
    response_model=List[AccountCharacterInstance],
    summary="List Account Character Inventory"
)
def list_account_characters(
    element: Optional[str] = Query(default=None, description="Filter by element"),
    min_level: Optional[int] = Query(default=None, ge=1, le=90, description="Filter by min level"),
    constellation: Optional[int] = Query(default=None, ge=0, le=6, description="Filter by constellation"),
    weapon_type: Optional[str] = Query(default=None, description="Filter by weapon type"),
):
    """List normalized characters owned in the player's account."""
    snapshot = account_inventory_service.get_active_snapshot()
    if not snapshot:
        return []
    chars = snapshot.characters
    if element:
        chars = [c for c in chars if c.element and c.element.lower() == element.lower()]
    if min_level is not None:
        chars = [c for c in chars if c.level >= min_level]
    if constellation is not None:
        chars = [c for c in chars if c.constellation == constellation]
    if weapon_type:
        chars = [c for c in chars if c.weapon_type and c.weapon_type.lower() == weapon_type.lower()]
    return chars


@router.get(
    "/account/weapons",
    response_model=List[AccountWeaponInstance],
    summary="List Account Weapon Instances"
)
def list_account_weapons(
    canonical_id: Optional[str] = Query(default=None, description="Filter by canonical weapon ID or slug"),
    name: Optional[str] = Query(default=None, description="Filter by weapon name"),
    weapon_type: Optional[str] = Query(default=None, description="Sword, Claymore, Polearm, Bow, Catalyst"),
    rarity: Optional[int] = Query(default=None, ge=1, le=5),
    equipped_only: bool = Query(default=False),
    character: Optional[str] = Query(default=None, description="Filter by equipped character"),
):
    """List distinct weapon instances in inventory and equipped on characters."""
    snapshot = account_inventory_service.get_active_snapshot()
    if not snapshot:
        return []
    weapons = snapshot.weapons
    if canonical_id:
        c_str = str(canonical_id).lower().replace("-", "_").replace(" ", "_")
        weapons = [
            w for w in weapons
            if (w.canonical_id is not None and str(w.canonical_id).lower() == c_str)
            or (w.canonical_name and c_str in w.canonical_name.lower().replace("'", "").replace(" ", "_"))
            or (w.good_key and c_str in w.good_key.lower())
        ]
    if name:
        weapons = [w for w in weapons if w.canonical_name and name.lower() in w.canonical_name.lower()]
    if weapon_type:
        weapons = [w for w in weapons if w.weapon_type and w.weapon_type.lower() == weapon_type.lower()]
    if rarity is not None:
        weapons = [w for w in weapons if w.rarity == rarity]
    if equipped_only:
        weapons = [w for w in weapons if w.location]
    if character:
        weapons = [w for w in weapons if w.location and character.lower() in w.location.lower()]
    return weapons


@router.get(
    "/account/artifacts",
    response_model=List[AccountArtifactInstance],
    summary="List Account Artifact Instances"
)
def list_account_artifacts(
    set_id: Optional[str] = Query(default=None, description="Filter by canonical set ID or slug"),
    set_name: Optional[str] = Query(default=None, description="Filter by artifact set name"),
    slot: Optional[str] = Query(default=None, description="flower, plume, sands, goblet, circlet"),
    rarity: Optional[int] = Query(default=None, ge=1, le=5),
    equipped_only: bool = Query(default=False),
    character: Optional[str] = Query(default=None, description="Filter by equipped character"),
):
    """List distinct artifact instances with roll substats and equipment locations."""
    snapshot = account_inventory_service.get_active_snapshot()
    if not snapshot:
        return []
    artifacts = snapshot.artifacts
    if set_id:
        s_str = str(set_id).lower().replace("-", "_").replace(" ", "_")
        artifacts = [
            a for a in artifacts
            if (a.canonical_set_id is not None and str(a.canonical_set_id).lower() == s_str)
            or (a.canonical_set_name and s_str in a.canonical_set_name.lower().replace("'", "").replace(" ", "_"))
            or (a.good_set_key and s_str in a.good_set_key.lower())
        ]
    if set_name:
        artifacts = [a for a in artifacts if a.canonical_set_name and set_name.lower() in a.canonical_set_name.lower()]
    if slot:
        artifacts = [a for a in artifacts if a.slot.lower() == slot.lower()]
    if rarity is not None:
        artifacts = [a for a in artifacts if a.rarity == rarity]
    if equipped_only:
        artifacts = [a for a in artifacts if a.location]
    if character:
        artifacts = [a for a in artifacts if a.location and character.lower() in a.location.lower()]
    return artifacts


@router.get(
    "/account/materials",
    response_model=List[AccountMaterialInstance],
    summary="List Account Material Inventory"
)
def list_account_materials(
    category: Optional[str] = Query(default=None, description="Material category"),
    search: Optional[str] = Query(default=None, description="Search by name or ID"),
    resolved_only: bool = Query(default=False),
    unresolved_only: bool = Query(default=False),
):
    """List materials and currencies in inventory with quantities."""
    snapshot = account_inventory_service.get_active_snapshot()
    if not snapshot:
        return []
    mats = snapshot.materials
    if search:
        s_lower = search.lower()
        mats = [m for m in mats if (m.canonical_name and s_lower in m.canonical_name.lower()) or (s_lower in m.good_key.lower())]
    if category:
        mats = [m for m in mats if m.material_type and category.lower() in m.material_type.lower()]
    if resolved_only:
        mats = [m for m in mats if m.resolution_status != ResolutionStatus.UNRESOLVED]
    if unresolved_only:
        mats = [m for m in mats if m.resolution_status == ResolutionStatus.UNRESOLVED]
    return mats


@router.post(
    "/account/import",
    response_model=AccountSummary,
    dependencies=[Depends(require_admin_auth)],
    summary="Import GOOD v3 Account Inventory JSON"
)
def import_account_inventory(
    payload: Dict[str, Any],
    account_uid: Optional[str] = Query(default=None, description="Optional player UID to bind"),
):
    """Ingest raw GOOD v3 JSON payload; validates, normalizes, and saves snapshot."""
    try:
        snapshot = account_inventory_service.import_good_payload(payload, account_uid=account_uid)
        return account_inventory_service.get_summary(snapshot)
    except AccountInventoryException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to process GOOD export: {e}")


@router.post(
    "/account/diff",
    response_model=AccountDiff,
    summary="Diff GOOD v3 Export Against Active Snapshot"
)
def diff_account_inventory(
    payload: Dict[str, Any]
):
    """Compare an imported GOOD payload against the active snapshot to detect changes."""
    active = account_inventory_service.get_active_snapshot()
    if not active:
        raise HTTPException(status_code=400, detail="No active baseline snapshot found to compare against.")
    try:
        valid_json, source_hash = account_inventory_service.validate_and_parse_good_payload(payload)
        candidate = account_inventory_service.normalize_good_to_snapshot(valid_json, source_hash)
        return account_inventory_service.compute_diff(active, candidate)
    except AccountInventoryException as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to diff payload: {e}")


# ==============================================================================
# Phase 7: Deterministic Build & Stat Engine Endpoints
# ==============================================================================

@router.get(
    "/build/{character_id}",
    response_model=CharacterBuildSnapshot,
    summary="Get Deterministic Character Build Snapshot"
)
def get_build_snapshot(
    character_id: str,
    game_version: Optional[str] = Query(default=None, description="Target game version for calculation, e.g. '5.4' or '7.0'. If omitted, evaluated as missing version metadata.")
):
    """
    Retrieve full deterministic build snapshot for an owned or canonical character.
    Calculates base layers, equipped weapon, equipped artifacts, set bonuses, and derived stats.
    """
    # 1. Attempt lookup from owned account snapshot
    build = stat_engine_service.get_account_character_build(character_id, game_version=game_version)
    if build:
        return build

    # 2. Fall back to canonical character calculation (baseline Lv90 build)
    char = game_data_service.get_character(character_id.lower())
    if not char:
        raise HTTPException(status_code=404, detail=f"Character '{character_id}' not found in account or canonical database.")

    return stat_engine_service.calculate_build_stats(char.name, game_version=game_version)


@router.get(
    "/build/{character_id}/stats",
    response_model=CalculatedCombatStats,
    summary="Get Calculated Combat Stats"
)
def get_build_stats(
    character_id: str,
    game_version: Optional[str] = Query(default=None, description="Target game version for calculation")
):
    """Retrieve only the calculated combat stats sheet for a character."""
    build = get_build_snapshot(character_id, game_version=game_version)
    return build.stats


@router.get(
    "/build/{character_id}/breakdown",
    response_model=FullStatBreakdown,
    summary="Get Full Mathematical Stat Breakdown"
)
def get_build_breakdown(
    character_id: str,
    game_version: Optional[str] = Query(default=None, description="Target game version for calculation")
):
    """Retrieve complete auditable breakdown of base, percent, flat, and slot contributions."""
    build = get_build_snapshot(character_id, game_version=game_version)
    return build.breakdown


@router.post(
    "/build/calculate",
    response_model=CharacterBuildSnapshot,
    summary="Calculate Ad-Hoc Character Build"
)
def calculate_ad_hoc_build(
    payload: CustomBuildRequest
):
    """
    Deterministically calculate combat stats for specified character, weapon, and artifact gear.
    All base stats and scaling are derived solely from trusted server-side canonical data.
    Client-injected arbitrary stats (e.g. base_atk, crit_rate) are strictly forbidden (HTTP 422).
    """
    # Validate account grounding if instance IDs supplied
    inv = account_inventory_service.get_active_snapshot()
    is_account_grounded = True

    if payload.account_character_instance_id:
        if not inv:
            raise HTTPException(
                status_code=400,
                detail="No active account snapshot available to validate character instance."
            )
        char_match = any(
            c.canonical_name.lower() == payload.account_character_instance_id.lower() or
            c.good_key.lower() == payload.account_character_instance_id.lower() or
            (c.canonical_id and str(c.canonical_id) == str(payload.account_character_instance_id))
            for c in inv.characters
        )
        if not char_match:
            raise HTTPException(
                status_code=400,
                detail=f"Character instance '{payload.account_character_instance_id}' is not owned in active account snapshot."
            )
    else:
        is_account_grounded = False

    art_dicts = []
    for art in payload.artifacts:
        if art.account_instance_id:
            if not inv:
                raise HTTPException(
                    status_code=400,
                    detail="No active account snapshot available to validate artifact instance."
                )
            found_art = any(getattr(a, "account_instance_id", None) == art.account_instance_id for a in inv.artifacts)
            if not found_art:
                raise HTTPException(
                    status_code=400,
                    detail=f"Artifact instance '{art.account_instance_id}' not found in active account snapshot."
                )
        else:
            is_account_grounded = False

        art_dicts.append({
            "slot": art.slot,
            "canonical_set_name": art.set_name,
            "set_name": art.set_name,
            "rarity": art.rarity,
            "level": art.level,
            "main_stat_key": art.main_stat_key,
            "substats": [s.model_dump() for s in art.substats],
            "account_instance_id": art.account_instance_id,
        })

    snapshot = stat_engine_service.calculate_build_stats(
        character_name_or_id=payload.character,
        char_level=payload.level,
        char_ascension=payload.ascension,
        char_constellation=payload.constellation,
        weapon_name_or_id=payload.weapon,
        weapon_level=payload.weapon_level,
        weapon_ascension=payload.weapon_ascension,
        weapon_refinement=payload.weapon_refinement,
        artifacts=art_dicts,
        talents=payload.talents,
        game_version=payload.game_version,
    )

    snapshot.build_type = "ACCOUNT_OWNED" if is_account_grounded else "HYPOTHETICAL_CANONICAL"
    snapshot.is_account_grounded = is_account_grounded
    return snapshot


@router.post(
    "/build/compare",
    response_model=BuildComparison,
    summary="Compare Two Character Builds"
)
def compare_character_builds(
    payload: Dict[str, Any]
):
    """
    Compare Build A vs Build B and compute exact mathematical deltas.
    Payload should contain 'build_a' and 'build_b' definitions (or character_a, weapon_a, character_b, weapon_b).
    """
    try:
        if "build_a" in payload and "build_b" in payload:
            b_a = stat_engine_service.calculate_build_stats(
                character_name_or_id=payload["build_a"]["character"],
                char_level=payload["build_a"].get("level", 90),
                weapon_name_or_id=payload["build_a"].get("weapon"),
                weapon_level=payload["build_a"].get("weapon_level", 90),
                weapon_refinement=payload["build_a"].get("weapon_refinement", 1),
                artifacts=payload["build_a"].get("artifacts", []),
            )
            b_b = stat_engine_service.calculate_build_stats(
                character_name_or_id=payload["build_b"]["character"],
                char_level=payload["build_b"].get("level", 90),
                weapon_name_or_id=payload["build_b"].get("weapon"),
                weapon_level=payload["build_b"].get("weapon_level", 90),
                weapon_refinement=payload["build_b"].get("weapon_refinement", 1),
                artifacts=payload["build_b"].get("artifacts", []),
            )
        else:
            char_a = payload.get("character_a")
            char_b = payload.get("character_b") or char_a
            if not char_a:
                raise HTTPException(status_code=400, detail="Missing character specification for comparison.")
            b_a = stat_engine_service.calculate_build_stats(char_a, weapon_name_or_id=payload.get("weapon_a"))
            b_b = stat_engine_service.calculate_build_stats(char_b, weapon_name_or_id=payload.get("weapon_b"))

        return stat_engine_service.compare_builds(b_a, b_b)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Comparison failed: {e}")


# Phase 1: Account Showcase Endpoints
@router.get(
    "/account/{uid}",
    response_model=EnkaShowcaseResponse,
    summary="Get Player Account Showcase"
)
async def get_player_account(
    uid: str,
    refresh: bool = Query(
        default=False,
        description="Force bypass cache"
    )
):
    """Retrieve and parse a player's public showcase data."""
    return await account_service.get_showcase(uid=uid, force_refresh=refresh)


@router.post(
    "/account/{uid}/refresh",
    response_model=EnkaShowcaseResponse,
    dependencies=[Depends(require_admin_auth)],
    summary="Force Refresh Player Showcase"
)
async def refresh_player_account(uid: str):
    """Force cache invalidation and query Enka.Network."""
    return await account_service.get_showcase(uid=uid, force_refresh=True)


@router.get(
    "/account/{uid}/characters",
    response_model=List[CharacterBuild],
    summary="List Player Showcase Characters"
)
async def list_showcase_characters(uid: str):
    """List all normalized character builds in the player's showcase."""
    showcase = await account_service.get_showcase(uid=uid)
    return showcase.characters


@router.get(
    "/account/{uid}/character/{character_ident}",
    response_model=CharacterBuild,
    summary="Get Specific Character Build"
)
async def get_character_build(uid: str, character_ident: str):
    """Retrieve detailed build for a specific character."""
    char = await account_service.get_character_build(
        uid=uid,
        character_identifier=character_ident
    )
    if not char:
        raise HTTPException(
            status_code=404,
            detail=(
                f"Character '{character_ident}' not found "
                f"in showcase for UID {uid}."
            )
        )
    return char


# Phase 2: Structured Genshin Data Endpoints
@router.get(
    "/data/characters",
    response_model=List[CharacterData],
    summary="List Canonical Characters"
)
def list_characters(
    element: Optional[str] = Query(
        default=None,
        description="Filter by Element (Pyro, Hydro, etc.)"
    ),
    weapon_type: Optional[str] = Query(
        default=None,
        description="Filter by Weapon Type"
    ),
    rarity: Optional[int] = Query(
        default=None,
        description="Filter by Rarity (4 or 5)"
    ),
):
    """Retrieve canonical characters list with optional filters."""
    return game_data_service.list_characters(
        element=element,
        weapon_type=weapon_type,
        rarity=rarity
    )


@router.get(
    "/data/characters/{name_or_id}",
    response_model=CharacterData,
    summary="Get Canonical Character Details"
)
def get_character_detail(name_or_id: str):
    """Retrieve detailed canonical character information."""
    char = game_data_service.get_character(name_or_id)
    if not char:
        raise HTTPException(
            status_code=404,
            detail=f"Character '{name_or_id}' not found in database."
        )
    return char


@router.get(
    "/data/weapons",
    response_model=List[WeaponData],
    summary="List Canonical Weapons"
)
def list_weapons(
    weapon_type: Optional[str] = Query(
        default=None,
        description="Filter by Weapon Type"
    ),
    rarity: Optional[int] = Query(
        default=None,
        description="Filter by Rarity"
    ),
):
    """Retrieve canonical weapons list with optional filters."""
    return game_data_service.list_weapons(
        weapon_type=weapon_type,
        rarity=rarity
    )


@router.get(
    "/data/weapons/{name_or_id}",
    response_model=WeaponData,
    summary="Get Canonical Weapon Details"
)
def get_weapon_detail(name_or_id: str):
    """Retrieve detailed canonical weapon information."""
    weapon = game_data_service.get_weapon(name_or_id)
    if not weapon:
        raise HTTPException(
            status_code=404,
            detail=f"Weapon '{name_or_id}' not found in database."
        )
    return weapon


@router.get(
    "/data/artifacts",
    response_model=List[ArtifactSetData],
    summary="List Canonical Artifact Sets"
)
def list_artifact_sets():
    """Retrieve canonical artifact sets with 2pc and 4pc bonuses."""
    return game_data_service.list_artifact_sets()


@router.get(
    "/data/artifacts/{name_or_id}",
    response_model=ArtifactSetData,
    summary="Get Canonical Artifact Set Details"
)
def get_artifact_detail(name_or_id: str):
    """Retrieve detailed artifact set bonuses and piece names."""
    art = game_data_service.get_artifact_set(name_or_id)
    if not art:
        raise HTTPException(
            status_code=404,
            detail=f"Artifact set '{name_or_id}' not found in database."
        )
    return art


@router.get(
    "/data/materials",
    response_model=List[MaterialData],
    summary="List Canonical Materials"
)
def list_materials(
    type: Optional[str] = Query(
        default=None,
        description="Filter by material type"
    )
):
    """Retrieve canonical materials list."""
    return game_data_service.list_materials(material_type=type)


@router.get(
    "/data/search",
    response_model=List[SearchResult],
    summary="Unified Game Data Search"
)
def search_game_data(
    q: str = Query(
        ...,
        min_length=1,
        description="Search keyword"
    )
):
    """Search across characters, weapons, artifact sets, and materials."""
    return game_data_service.search(query=q)


@router.get(
    "/data/manifest",
    response_model=DataProvenanceManifest,
    summary="Get Data Provenance Manifest"
)
def get_data_manifest():
    """Return the current provenance snapshot for local datasets."""
    return provenance_service.build_manifest()


# Canonical Data Refresh & Acquisition Pipeline Endpoints
@router.get(
    "/data/pipeline/status",
    response_model=DatasetVersionState,
    summary="Get Canonical Data Pipeline Version State"
)
def get_pipeline_version_state():
    """Return the decoupled version status across detection, availability, verification, and canonical active status."""
    return canonical_data_pipeline.get_version_state()


@router.get(
    "/data/pipeline/versions",
    summary="List Stored Dataset Versions"
)
def list_pipeline_versions():
    """Return all available and verified historical versioned datasets."""
    return {
        "active_canonical_version": canonical_data_pipeline.get_active_version(),
        "available_versions": canonical_data_pipeline.list_available_dataset_versions(),
        "verified_versions": canonical_data_pipeline.list_verified_dataset_versions(),
    }


@router.post(
    "/data/pipeline/simulate-refresh",
    dependencies=[Depends(require_admin_auth)],
    summary="Simulate Canonical Data Refresh Pipeline"
)
def simulate_pipeline_refresh(
    target_version: str = Query(default="7.0", description="Target version to simulate refresh for"),
    auto_promote: bool = Query(default=False, description="Whether to automatically promote if validation gates pass")
):
    """Execute simulated 12-step data refresh pipeline with validation gates."""
    return canonical_data_pipeline.execute_refresh_pipeline(
        target_version=target_version,
        auto_promote=auto_promote,
    )


@router.get(
    "/data/pipeline/discover",
    summary="Discover Upstream Dataset Version"
)
def discover_pipeline_version():
    """Query live upstream primary source (DimbreathBot/AnimeGameData) for newly released datasets."""
    return canonical_data_pipeline.discover_upstream_dataset_version()


@router.get(
    "/data/pipeline/diff",
    summary="Get Deterministic Version Diff"
)
def get_pipeline_version_diff(
    base_version: str = Query(default="5.4", description="Base historical version"),
    target_version: str = Query(default="7.0", description="Target comparison version")
):
    """Generate or retrieve deterministic diff between base and target dataset versions."""
    return canonical_data_pipeline.generate_version_diff(base_version=base_version, target_version=target_version)


@router.post(
    "/data/pipeline/refresh",
    dependencies=[Depends(require_admin_auth)],
    summary="Execute Live Canonical Data Refresh Pipeline"
)
def execute_pipeline_refresh(
    target_version: Optional[str] = Query(default=None, description="Optional explicit version; if omitted, automatically discovered"),
    auto_promote: bool = Query(default=True, description="Whether to promote to active canonical pointer if validation passes")
):
    """Execute live 12-step data refresh pipeline against upstream repositories with fail-closed gates."""
    return canonical_data_pipeline.execute_refresh_pipeline(
        target_version=target_version,
        auto_promote=auto_promote,
    )


@router.post(
    "/data/pipeline/rollback",
    dependencies=[Depends(require_admin_auth)],
    summary="Rollback Canonical Dataset Version"
)
def rollback_pipeline_version(
    target_version: str = Query(..., description="Verified historical version to rollback to, e.g. '5.4'")
):
    """Rollback active canonical dataset pointer to a verified historical version."""
    success, msg = canonical_data_pipeline.rollback_to_version(target_version)
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "active_version": canonical_data_pipeline.get_active_version(),
        "message": msg,
    }


# Version Completeness & Phase Gate Endpoints
@router.get(
    "/data/version-completeness",
    response_model=VersionCompletenessReport,
    summary="Get Multi-Domain Version Completeness Report"
)
def get_version_completeness_report(
    target_version: Optional[str] = Query(default=None, description="Optional target version, defaults to active canonical version")
):
    """
    Audit and return version completeness across:
    1. Structured Canonical Game Data (Characters, Weapons, Artifacts, Materials, Curves)
    2. Game Content (Quests, Events, Domains, Enemies, Regions, Achievements, Recipes)
    3. Curated Knowledge Base (Character Guides, Weapon Guides, Theorycrafting, Patch notes)
    4. Provenance Integrity
    5. Freshness
    6. Version Delta Coverage
    """
    return version_completeness_gate.audit_version_completeness(target_version=target_version)


@router.get(
    "/project/phase-gate",
    response_model=PhaseGateResponse,
    summary="Evaluate Phase 8 Release Gate"
)
def evaluate_project_phase_gate():
    """
    Hard architectural gate:
    Evaluates whether Phase 8+ is permitted to begin based on 100% verified version completeness
    for the latest live Genshin Impact version. Returns fail-closed blockers if incomplete.
    """
    return version_completeness_gate.evaluate_phase_gate()


@router.get(
    "/data/knowledge-contract",
    summary="Get Formal GenshinIQ Knowledge Contract"
)
def get_knowledge_contract():
    """
    Returns the formal, version-controlled GenshinIQ Knowledge Contract
    specifying product capabilities, required domains, fields, quality states,
    and source derivation rules.
    """
    return knowledge_contract_service.get_contract()


@router.get(
    "/pipeline/update-manifests",
    summary="List Version Update Manifests"
)
def list_update_manifests():
    """Returns all recorded version update manifests detailing lifecycle progression."""
    manifest_dir = Path("data/canonical/update_manifests")
    manifests = []
    if manifest_dir.exists():
        for f in sorted(manifest_dir.glob("*_manifest.json")):
            try:
                with open(f, "r", encoding="utf-8") as jf:
                    manifests.append(json.load(jf))
            except Exception:
                pass
    return manifests


@router.get(
    "/pipeline/delta",
    summary="Get Version Delta Report"
)
def get_version_delta_report(
    base_version: str = Query(default="5.4", description="Base version to compare from"),
    candidate_version: str = Query(default="7.0", description="Candidate version to compare to"),
):
    """Computes fine-grained entity and attribute differences between two versions."""
    base_dir = Path("data/processed/game_data/versions") / base_version
    cand_dir = Path("data/processed/game_data/versions") / candidate_version
    if not cand_dir.exists():
        cand_dir = Path("data/processed/game_data")

    base_chars, cand_chars = {}, {}
    if (base_dir / "characters.json").exists():
        with open(base_dir / "characters.json", "r", encoding="utf-8") as f:
            base_chars = {str(c.get("id")): c for c in json.load(f)}
    if (cand_dir / "characters.json").exists():
        with open(cand_dir / "characters.json", "r", encoding="utf-8") as f:
            cand_chars = {str(c.get("id")): c for c in json.load(f)}

    delta = version_delta_service.compare_version_datasets(
        base_version=base_version,
        candidate_version=candidate_version,
        base_characters=base_chars,
        candidate_characters=cand_chars,
    )
    return delta.model_dump()




# Phase 3: Central Source Registry Endpoints
@router.get(
    "/sources",
    response_model=List[Source],
    summary="List Registered Sources"
)
def list_sources(
    tier: Optional[SourceTier] = Query(
        default=None,
        description="Filter by authority tier (1 to 5)"
    ),
    enabled_only: bool = Query(
        default=True,
        description="Only return active enabled sources"
    ),
):
    """Retrieve canonical sources in the GenshinIQ provenance registry."""
    return source_registry_service.list_sources(tier=tier, enabled_only=enabled_only)


@router.get(
    "/sources/{source_id}",
    response_model=Source,
    summary="Get Specific Source"
)
def get_source(source_id: str):
    """Retrieve details for a specific canonical data or knowledge source."""
    source = source_registry_service.get_source(source_id)
    if not source:
        raise HTTPException(
            status_code=404,
            detail=f"Source with ID '{source_id}' not found in registry."
        )
    return source


# Phase 3: Curated Knowledge Base Endpoints
@router.get(
    "/knowledge/documents",
    response_model=List[KnowledgeDocument],
    summary="List Curated Knowledge Documents"
)
def list_knowledge_documents(
    character: Optional[str] = Query(
        default=None,
        description="Filter by associated Character name"
    ),
    topic: Optional[str] = Query(
        default=None,
        description="Filter by topic (e.g. Character Guide, Mechanics)"
    ),
    source_type: Optional[SourceType] = Query(
        default=None,
        description="Filter by source classification"
    ),
    source_id: Optional[str] = Query(
        default=None,
        description="Filter by registered source ID"
    ),
    authority_tier: Optional[int] = Query(
        default=None,
        description="Filter by authority tier (1 to 5)"
    ),
    game_version: Optional[str] = Query(
        default=None,
        description="Filter by game version"
    ),
):
    """Retrieve list of curated knowledge articles with optional filters."""
    return knowledge_service.list_documents(
        character=character,
        topic=topic,
        source_type=source_type,
        source_id=source_id,
        authority_tier=authority_tier,
        game_version=game_version
    )


@router.get(
    "/knowledge/documents/{doc_id}",
    response_model=KnowledgeDocument,
    summary="Get Specific Knowledge Document"
)
def get_knowledge_document(doc_id: str):
    """Retrieve full text and metadata for a specific knowledge article."""
    doc = knowledge_service.get_document(doc_id)
    if not doc:
        raise HTTPException(
            status_code=404,
            detail=f"Knowledge document with ID '{doc_id}' not found."
        )
    return doc


@router.get(
    "/knowledge/search",
    response_model=List[KnowledgeSearchResult],
    summary="Search Knowledge Base"
)
def search_knowledge_base(
    q: str = Query(
        ...,
        min_length=1,
        description="Search query keyword"
    ),
    limit: int = Query(
        default=5,
        description="Max number of search results to return"
    ),
):
    """Perform keyword search across knowledge base documents."""
    return knowledge_service.search_documents(query=q, limit=limit)


@router.get(
    "/knowledge/retrieve",
    response_model=EvidenceBundle,
    summary="Retrieve Evidence Bundle (Phase 5)"
)
def retrieve_evidence_bundle(
    q: str = Query(
        ...,
        min_length=1,
        description="Query string for hybrid semantic and lexical retrieval"
    ),
    mode: Optional[str] = Query(
        default=None,
        description="Explicit retrieval mode (mechanics, weapon, artifact, character, farming, historical, etc.)"
    ),
    top_k: int = Query(
        default=5,
        ge=1,
        le=30,
        description="Max number of ranked evidence chunks to return"
    ),
    character: Optional[str] = Query(
        default=None,
        description="Optional filter by character name"
    ),
    tier: Optional[int] = Query(
        default=None,
        ge=1,
        le=5,
        description="Optional maximum authority tier filter"
    ),
):
    """Production hybrid evidence retrieval with signals, provenance, and freshness ranking."""
    return retrieval_service.retrieve(
        query=q,
        mode=mode,
        top_k=top_k,
        character_filter=character,
        tier_filter=tier,
    )


# Phase 4 & 5: Assistant Chat Endpoint
@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Grounded Chat Assistant"
)
async def chat_assistant(request: ChatRequest):
    """
    Query understanding and retrieval-augmented generation grounded
    in curated guides and optional player showcase build details.
    """
    uid = request.uid or settings.USER_UID
    return await rag_service.generate_response(
        messages=request.messages,
        uid=uid
    )


# -----------------------------------------------------------------------------
# Formal Character Knowledge Package & Gaps Endpoints
# -----------------------------------------------------------------------------
@router.get(
    "/knowledge/character-packages",
    summary="List all 119 Character Knowledge Packages"
)
def list_character_knowledge_packages():
    """Returns summary of all compiled character knowledge packages with quality states."""
    from backend.services.character_knowledge_service import character_knowledge_service
    packages = character_knowledge_service.list_all_packages()
    return [
        {
            "character_id": p.character_id,
            "character_name": p.character_name,
            "quality_state": p.quality_state,
            "is_released": p.is_released,
            "derived_calculations_count": len(p.derived_calculations),
            "knowledge_gaps_count": len(p.knowledge_gaps),
            "provenance_sources": p.provenance_sources,
        }
        for p in packages
    ]


@router.get(
    "/knowledge/character-package/{id_or_name}",
    summary="Get Detailed Character Knowledge Package"
)
def get_character_knowledge_package(id_or_name: str):
    """Returns the full granular knowledge package including deterministic fields, curated fields, and gaps."""
    from backend.services.character_knowledge_service import character_knowledge_service
    pkg = character_knowledge_service.get_character_package(id_or_name)
    if not pkg:
        raise HTTPException(status_code=404, detail=f"Character '{id_or_name}' not found")
    return pkg.model_dump()


@router.get(
    "/knowledge/gaps",
    summary="Get Cataloged Knowledge Gaps"
)
def get_knowledge_gaps():
    """Returns registered knowledge gaps from data/canonical/knowledge_gaps.json."""
    gaps_path = Path("data/canonical/knowledge_gaps.json")
    if not gaps_path.exists():
        return {"total_gaps_tracked": 0, "gaps": []}
    with open(gaps_path, "r", encoding="utf-8") as f:
        return json.load(f)
