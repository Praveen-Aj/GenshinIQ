"""Source Adapters package for GenshinIQ data acquisition."""

from backend.adapters.base import (
    AdapterDiscoveredItem,
    AdapterValidationResult,
    SourceAdapter,
    VersionLifecycleState,
)
from backend.adapters.official_adapter import OfficialSourceAdapter
from backend.adapters.animegamedata_adapter import AnimeGameDataAdapter
from backend.adapters.project_amber_adapter import ProjectAmberAdapter
from backend.adapters.kqm_adapter import KQMAdapter
from backend.adapters.tcl_adapter import TCLAdapter
from backend.adapters.enka_adapter import EnkaAdapter
from backend.adapters.good_adapter import GOODAdapter

__all__ = [
    "AdapterDiscoveredItem",
    "AdapterValidationResult",
    "SourceAdapter",
    "VersionLifecycleState",
    "OfficialSourceAdapter",
    "AnimeGameDataAdapter",
    "ProjectAmberAdapter",
    "KQMAdapter",
    "TCLAdapter",
    "EnkaAdapter",
    "GOODAdapter",
]
