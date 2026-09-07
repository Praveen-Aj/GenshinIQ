"""Service managing validated Genshin Impact game versions, patch history, and staleness detection."""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from backend.config import settings
from backend.models.version import (
    GameVersion,
    VersionStatus,
    StalenessEvaluation,
)

logger = logging.getLogger(__name__)

VERSIONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "canonical" / "game_versions.json"


def parse_version_tuple(ver_str: str) -> Tuple[int, int]:
    """Parse version string like '5.4' into a comparable tuple (5, 4)."""
    try:
        parts = ver_str.strip().lstrip("v").split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return (major, minor)
    except Exception:
        return (0, 0)


class VersionService:
    """Manages the canonical game version registry and staleness policies."""

    def __init__(self, versions_path: Optional[Path] = None):
        self.versions_path = versions_path or VERSIONS_FILE
        self._versions: Dict[str, GameVersion] = {}
        self._current_version: Optional[GameVersion] = None
        self._version_order: List[str] = []
        self.load_versions()

    def load_versions(self) -> None:
        """Load and validate all game versions from canonical registry."""
        self._versions.clear()
        self._version_order.clear()
        self._current_version = None

        if not self.versions_path.exists():
            logger.error(f"Game versions registry missing at {self.versions_path}")
            return

        try:
            with open(self.versions_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            for item in data:
                gv = GameVersion.model_validate(item)
                self._versions[gv.version] = gv
                self._version_order.append(gv.version)
                if gv.is_current:
                    self._current_version = gv

            # Fallback if no explicit is_current flag was set
            if not self._current_version and self._version_order:
                self._current_version = self._versions[self._version_order[-1]]

        except Exception as e:
            logger.error(f"Failed to load game versions registry: {e}")

    def get_current_version(self) -> GameVersion:
        """Return the validated current live game version."""
        if not self._current_version:
            self.load_versions()
        if not self._current_version:
            # Absolute fallback to verified 5.4
            return GameVersion(
                version="5.4",
                name="Dreams of Light Upon the Flowing Star",
                release_date="2025-02-12",
                major_region="Chenyu Vale / Natlan",
                is_current=True,
                is_upcoming=False,
            )
        return self._current_version

    def list_versions(self, reverse: bool = True) -> List[GameVersion]:
        """List all tracked game versions in chronological order."""
        ordered = [self._versions[v] for v in self._version_order if v in self._versions]
        return list(reversed(ordered)) if reverse else ordered

    def get_version(self, version_str: str) -> Optional[GameVersion]:
        """Look up metadata for a specific version string."""
        clean_v = version_str.strip().lstrip("v")
        return self._versions.get(clean_v)

    def calculate_distance(self, entity_version: str, target_version: Optional[str] = None) -> int:
        """Calculate the number of patch versions between an entity version and current target version."""
        target = target_version or self.get_current_version().version
        clean_ent = entity_version.strip().lstrip("v")
        clean_target = target.strip().lstrip("v")

        if clean_ent not in self._version_order or clean_target not in self._version_order:
            # Fall back to tuple difference
            e_t = parse_version_tuple(clean_ent)
            t_t = parse_version_tuple(clean_target)
            return max(0, (t_t[0] - e_t[0]) * 10 + (t_t[1] - e_t[1]))

        idx_ent = self._version_order.index(clean_ent)
        idx_target = self._version_order.index(clean_target)
        return max(0, idx_target - idx_ent)

    def evaluate_staleness(
        self,
        entity_version: str,
        stale_threshold_patches: int = 4,
    ) -> StalenessEvaluation:
        """Evaluate if a document or entity is considered stale relative to the live version.
        
        A document is considered stale if:
        - It is more than `stale_threshold_patches` patches behind current.
        - For Natlan mechanics (v5.0+), any document pre-5.0 is considered stale for core mechanics.
        """
        curr = self.get_current_version().version
        clean_ent = entity_version.strip().lstrip("v")
        dist = self.calculate_distance(clean_ent, curr)
        is_curr = clean_ent == curr

        # Evaluation rules
        is_stale = False
        warning = None

        if dist > 0:
            if dist >= stale_threshold_patches or parse_version_tuple(clean_ent)[0] < parse_version_tuple(curr)[0]:
                is_stale = True
                warning = f"Document is from v{clean_ent} ({dist} patches behind current v{curr}). Verify newer character/weapon additions."
            else:
                warning = f"Verified for v{clean_ent} (Current: v{curr}). Mechanics may have received minor adjustments."

        return StalenessEvaluation(
            entity_version=clean_ent,
            current_version=curr,
            is_current=is_curr,
            is_stale=is_stale,
            version_distance=dist,
            warning=warning,
        )

    def get_status(
        self,
        total_documents: int = 0,
        stale_documents: int = 0,
        latest_canonical_update: str = "",
    ) -> VersionStatus:
        """Return the unified version status and system health summary."""
        curr = self.get_current_version()
        return VersionStatus(
            current_version=curr.version,
            patch_name=curr.name,
            release_date=curr.release_date,
            major_region=curr.major_region,
            app_version=settings.APP_VERSION,
            total_tracked_versions=len(self._versions),
            latest_canonical_update=latest_canonical_update or curr.release_date,
            stale_document_count=stale_documents,
            total_document_count=total_documents,
        )


version_service = VersionService()
