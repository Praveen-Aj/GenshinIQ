"""API routes for GenshinIQ."""

from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from backend.config import settings
from backend.services.account_service import account_service
from backend.services.game_data_service import game_data_service
from backend.models.account import EnkaShowcaseResponse, CharacterBuild
from backend.models.game_data import (
    CharacterData,
    WeaponData,
    ArtifactSetData,
    MaterialData,
    SearchResult,
)
from backend.models.provenance import DataProvenanceManifest
from backend.models.knowledge import (
    KnowledgeDocument,
    KnowledgeSearchResult,
    SourceType,
)
from backend.services.knowledge_service import knowledge_service
from backend.services.provenance_service import provenance_service
from backend.models.chat import ChatRequest, ChatResponse
from backend.services.rag_service import rag_service
from backend.models.version import GameVersion, VersionStatus, StalenessEvaluation
from backend.services.version_service import version_service

router = APIRouter()


# System Diagnostics
@router.get("/health", summary="Health Check")
async def health_check():
    """Health check endpoint to verify backend system status and active game version."""
    curr_v = version_service.get_current_version()
    return {
        "status": "ok",
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "game_version": curr_v.version,
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
