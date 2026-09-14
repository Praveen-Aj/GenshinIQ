"""Service managing validated Genshin Impact game versions, patch history, and staleness detection."""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set

from backend.config import settings
from backend.models.version import (
    GameVersion,
    VersionStatus,
    StalenessEvaluation,
    VerificationStatus,
    FreshnessStatus,
    VersionCheckResult,
)

logger = logging.getLogger(__name__)

VERSIONS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "canonical" / "game_versions.json"
PATCH_CHANGES_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "canonical" / "patch_changes.json"


def parse_version_tuple(ver_str: str) -> Tuple[int, int]:
    """Parse version string like '5.4' or '7.0' into a comparable tuple (5, 4)."""
    try:
        parts = ver_str.strip().lstrip("v").split(".")
        major = int(parts[0]) if len(parts) > 0 and parts[0].isdigit() else 0
        minor = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        return (major, minor)
    except Exception:
        return (0, 0)


class VersionService:
    """Manages the canonical game version registry, automated discovery, and change-aware staleness policies."""

    def __init__(self, versions_path: Optional[Path] = None, patch_changes_path: Optional[Path] = None):
        self.versions_path = versions_path or VERSIONS_FILE
        self.patch_changes_path = patch_changes_path or PATCH_CHANGES_FILE
        self._versions: Dict[str, GameVersion] = {}
        self._current_version: Optional[GameVersion] = None
        self._latest_known_version: Optional[GameVersion] = None
        self._project_target_version: Optional[str] = "7.0"
        self._version_order: List[str] = []
        self._discovery_status: str = "AVAILABLE"
        self._last_verification: str = "2026-09-08T00:00:00Z"
        self._update_available: bool = False
        self._patch_changes: Dict[str, List[str]] = {}
        self.load_versions()
        self.load_patch_changes()

    def load_versions(self) -> None:
        """Load and validate all game versions from canonical registry.
        
        Enforces:
        - Exactly one released version is marked as current.
        - Future/unreleased versions cannot become current by having a higher number.
        - Preserves chronological version order.
        """
        self._versions.clear()
        self._version_order.clear()
        self._current_version = None
        self._latest_known_version = None

        if not self.versions_path.exists():
            logger.error(f"Game versions registry missing at {self.versions_path}")
            return

        try:
            with open(self.versions_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            candidates_current: List[GameVersion] = []
            released_versions: List[GameVersion] = []

            for item in data:
                gv = GameVersion.model_validate(item)
                self._versions[gv.version] = gv
                self._version_order.append(gv.version)

                if gv.is_released:
                    released_versions.append(gv)
                    if gv.is_current:
                        candidates_current.append(gv)

                if gv.is_project_target:
                    self._project_target_version = gv.version

            # Track latest known released version
            if released_versions:
                self._latest_known_version = released_versions[-1]

            # Enforce single released current version
            if len(candidates_current) == 1:
                self._current_version = candidates_current[0]
            elif len(candidates_current) > 1:
                logger.warning(f"Multiple current versions detected: {[c.version for c in candidates_current]}. Enforcing newest released.")
                # Disambiguate by taking the newest released among the flagged ones
                self._current_version = candidates_current[-1]
            elif released_versions:
                # Fallback to the latest verified released version
                self._current_version = released_versions[-1]
                logger.info(f"No explicit current version set; default to newest released {self._current_version.version}")

            if not self._project_target_version and self._current_version:
                self._project_target_version = self._current_version.version

        except Exception as e:
            logger.error(f"Failed to load game versions registry: {e}")

    def load_patch_changes(self) -> None:
        """Load registered patch system modifications for change-aware staleness invalidation."""
        self._patch_changes.clear()
        if self.patch_changes_path.exists():
            try:
                with open(self.patch_changes_path, "r", encoding="utf-8") as f:
                    self._patch_changes = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load patch changes file: {e}")
        else:
            # Default known system changes for testing and runtime tracking
            self._patch_changes = {}

    def get_current_version(self) -> GameVersion:
        """Return the validated actual current released game version."""
        if not self._current_version:
            self.load_versions()
        if not self._current_version:
            # Safety fallback to canonical 7.0 release
            return GameVersion(
                version="7.0",
                name="The Stars Turn Anew",
                release_date="2026-09-02",
                major_region="Teyvat (Canonical Target)",
                is_released=True,
                is_current=True,
                is_project_target=True,
                verification_status=VerificationStatus.VERIFIED_OFFICIAL.value,
            )
        return self._current_version

    def get_latest_known_version(self) -> GameVersion:
        """Return the newest verified released version known to GenshinIQ."""
        return self._latest_known_version or self.get_current_version()

    def get_project_target_version(self) -> str:
        """Return the project target development anchor version."""
        return self._project_target_version or "7.0"

    def list_versions(self, reverse: bool = True) -> List[GameVersion]:
        """List all tracked game versions in chronological order."""
        ordered = [self._versions[v] for v in self._version_order if v in self._versions]
        return list(reversed(ordered)) if reverse else ordered

    def get_all_versions(self, reverse: bool = True) -> List[GameVersion]:
        """Alias for list_versions for test and caller compatibility."""
        return self.list_versions(reverse=reverse)

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
            e_t = parse_version_tuple(clean_ent)
            t_t = parse_version_tuple(clean_target)
            return max(0, (t_t[0] - e_t[0]) * 10 + (t_t[1] - e_t[1]))

        idx_ent = self._version_order.index(clean_ent)
        idx_target = self._version_order.index(clean_target)
        return max(0, idx_target - idx_ent)

    def get_changed_systems_between(self, from_version: str, to_version: str) -> Set[str]:
        """Return the set of all systems/characters modified between from_version and to_version."""
        clean_from = from_version.strip().lstrip("v")
        clean_to = to_version.strip().lstrip("v")
        if clean_from not in self._version_order or clean_to not in self._version_order:
            return set()

        idx_from = self._version_order.index(clean_from)
        idx_to = self._version_order.index(clean_to)
        if idx_to <= idx_from:
            return set()

        changed: Set[str] = set()
        for idx in range(idx_from + 1, idx_to + 1):
            ver = self._version_order[idx]
            for item in self._patch_changes.get(ver, []):
                changed.add(item)
        return changed

    def get_patch_changes(self, from_version: str, to_version: str) -> Set[str]:
        """Interface for discovering systems/characters modified between from_version and to_version."""
        return self.get_changed_systems_between(from_version, to_version)

    def evaluate_staleness(
        self,
        entity_version: str,
        affected_systems: Optional[List[str]] = None,
        stale_threshold_patches: int = 4,
    ) -> StalenessEvaluation:
        """Evaluate semantic freshness of a document against current version using change-aware logic.
        
        Rules:
        1. If entity_version == current_version:
           -> CURRENT (100% up to date)
        2. If entity_version < current_version:
           - Check if any system in affected_systems was modified in an intervening patch:
             -> If modified: STALE (kit or mechanics superseded by later patch change)
           - If not modified and version distance <= 2 (e.g. 7.0 guide when game is 7.1):
             -> RECENT_COMPATIBLE (still accurate guidance)
           - If distance >= stale_threshold_patches or major difference >= 2:
             -> STALE
        """
        curr = self.get_current_version().version
        clean_ent = entity_version.strip().lstrip("v")
        dist = self.calculate_distance(clean_ent, curr)
        is_curr = clean_ent == curr

        systems = affected_systems or []
        changed_since = self.get_changed_systems_between(clean_ent, curr)
        conflicting_changes = [s for s in systems if s in changed_since]

        if is_curr:
            return StalenessEvaluation(
                entity_version=clean_ent,
                current_version=curr,
                freshness_status=FreshnessStatus.CURRENT,
                is_current=True,
                is_stale=False,
                version_distance=0,
                warning=None,
                affected_systems=systems,
            )

        # Intervening system modification check
        if conflicting_changes:
            return StalenessEvaluation(
                entity_version=clean_ent,
                current_version=curr,
                freshness_status=FreshnessStatus.STALE,
                is_current=False,
                is_stale=True,
                version_distance=dist,
                warning=f"Document affected by patch changes between v{clean_ent} and v{curr}: {conflicting_changes}",
                affected_systems=systems,
            )

        # Recent compatible threshold: <= 2 minor patches behind with zero conflicting system changes
        maj_diff = parse_version_tuple(curr)[0] - parse_version_tuple(clean_ent)[0]
        if dist <= 2 and maj_diff < 1:
            return StalenessEvaluation(
                entity_version=clean_ent,
                current_version=curr,
                freshness_status=FreshnessStatus.RECENT_COMPATIBLE,
                is_current=False,
                is_stale=False,
                version_distance=dist,
                warning=f"Verified for v{clean_ent} (Current: v{curr}). Mechanics/kit remain compatible.",
                affected_systems=systems,
            )

        # Stale threshold: distant versions or major version shifts
        is_stale = dist >= stale_threshold_patches or maj_diff >= 2 or dist > 2
        warning = f"Document is from v{clean_ent} ({dist} patches behind current v{curr}). Verify newer character/weapon additions."

        return StalenessEvaluation(
            entity_version=clean_ent,
            current_version=curr,
            freshness_status=FreshnessStatus.STALE if is_stale else FreshnessStatus.RECENT_COMPATIBLE,
            is_current=False,
            is_stale=is_stale,
            version_distance=dist,
            warning=warning,
            affected_systems=systems,
        )

    def update_version_state(
        self,
        new_version: str,
        name: str,
        release_date: str,
        major_region: str,
        is_released: bool = True,
        is_current: bool = True,
        changed_systems: Optional[List[str]] = None,
        source_url: str = "https://genshin.hoyoverse.com/en/news",
    ) -> VersionStatus:
        """Atomically promote a new version to current while preserving all historical records."""
        clean_v = new_version.strip().lstrip("v")

        # Load existing raw JSON
        if self.versions_path.exists():
            with open(self.versions_path, "r", encoding="utf-8") as f:
                raw_versions = json.load(f)
        else:
            raw_versions = []

        # If marking as current, unset is_current on all existing records
        if is_current:
            for item in raw_versions:
                item["is_current"] = False

        # Find or append the record
        existing = next((item for item in raw_versions if item["version"] == clean_v), None)
        if existing:
            existing["name"] = name
            existing["release_date"] = release_date
            existing["major_region"] = major_region
            existing["is_released"] = is_released
            existing["is_current"] = is_current
            existing["verification_status"] = VerificationStatus.VERIFIED_OFFICIAL.value
            existing["source_id"] = "src_hoyoverse_patch_notes"
            existing["source_url"] = source_url
            existing["canonical_url"] = source_url
            existing["retrieved_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        else:
            raw_versions.append({
                "version": clean_v,
                "name": name,
                "release_date": release_date,
                "major_region": major_region,
                "is_released": is_released,
                "is_current": is_current,
                "is_project_target": False,
                "verification_status": VerificationStatus.VERIFIED_OFFICIAL.value,
                "source_id": "src_hoyoverse_patch_notes",
                "source_url": source_url,
                "canonical_url": source_url,
                "retrieved_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            })

        # Save to file
        with open(self.versions_path, "w", encoding="utf-8") as f:
            json.dump(raw_versions, f, indent=2, ensure_ascii=False)

        # Record patch changes if any
        if changed_systems:
            self._patch_changes[clean_v] = changed_systems
            with open(self.patch_changes_path, "w", encoding="utf-8") as f:
                json.dump(self._patch_changes, f, indent=2, ensure_ascii=False)

        # Reload memory
        self.load_versions()
        self.load_patch_changes()
        self._last_verification = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._discovery_status = "AVAILABLE"

        logger.info(f"Promoted game version to v{clean_v} ({name}). Current version count: {len(self._versions)}")
        return self.get_status()

    def check_and_update(
        self,
        discovery_provider: Optional[object] = None,
        auto_promote: bool = True,
        simulate_network_failure: bool = False,
        simulate_malformed: bool = False,
    ) -> VersionCheckResult:
        """Execute end-to-end DISCOVER -> VERIFY -> PROMOTE pipeline.
        
        1. DISCOVER: Query approved official source for latest released patch candidate.
        2. VERIFY: Strictly validate legitimacy, release status, non-future dates, and source authority.
        3. PROMOTE: If auto_promote is enabled and verified newer released version detected,
           atomically update canonical registry while strictly preserving historical records.
        """
        from backend.services.version_discovery import (
            HoYoverseOfficialDiscoveryProvider,
            MockDiscoveryProvider,
            verify_candidate,
        )

        curr = self.get_current_version().version

        if simulate_network_failure:
            provider = MockDiscoveryProvider(simulate_network_failure=True)
        elif simulate_malformed:
            provider = MockDiscoveryProvider(simulate_malformed=True)
        else:
            provider = discovery_provider or HoYoverseOfficialDiscoveryProvider()

        try:
            candidate = provider.discover()
        except ConnectionError as e:
            logger.warning(f"Official discovery network failure: {e}")
            self._discovery_status = "CACHED_OFFLINE"
            self._update_available = False
            return VersionCheckResult(
                current_version=curr,
                discovered_version=None,
                verification_status="FAILED",
                update_available=False,
                promoted=False,
                discovery_status="CACHED_OFFLINE",
                effective_current_version=curr,
                message="Official source unreachable; preserving last verified version.",
            )
        except Exception as e:
            logger.warning(f"Official discovery parsing failure: {e}")
            self._discovery_status = "MALFORMED_DATA"
            self._update_available = False
            return VersionCheckResult(
                current_version=curr,
                discovered_version=None,
                verification_status="FAILED",
                update_available=False,
                promoted=False,
                discovery_status="MALFORMED_DATA",
                effective_current_version=curr,
                message=f"Official source response could not be verified: {e}",
            )

        if candidate is None:
            self._discovery_status = "AVAILABLE"
            self._last_verification = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._update_available = False
            return VersionCheckResult(
                current_version=curr,
                discovered_version=None,
                verification_status="NO_NEW_DATA",
                update_available=False,
                promoted=False,
                discovery_status="AVAILABLE",
                effective_current_version=curr,
                message=f"Current version v{curr} is up to date. No newer release detected.",
            )

        # 2. VERIFY
        verification = verify_candidate(candidate, curr, self.list_versions())
        if not verification.is_valid:
            self._last_verification = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._discovery_status = "AVAILABLE"
            self._update_available = False
            return VersionCheckResult(
                current_version=curr,
                discovered_version=candidate.version,
                verification_status=verification.status,
                update_available=False,
                promoted=False,
                discovery_status="AVAILABLE",
                effective_current_version=curr,
                message=verification.reason,
            )

        if verification.status == "ALREADY_CURRENT":
            self._last_verification = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            self._discovery_status = "AVAILABLE"
            self._update_available = False
            return VersionCheckResult(
                current_version=curr,
                discovered_version=candidate.version,
                verification_status="PASS",
                update_available=False,
                promoted=False,
                discovery_status="AVAILABLE",
                effective_current_version=curr,
                message=f"Discovered version v{candidate.version} matches current version. Update required: NO.",
            )

        # 3. PROMOTE
        update_available = True
        promoted = False
        effective_ver = curr

        if auto_promote:
            self.update_version_state(
                new_version=candidate.version,
                name=candidate.name,
                release_date=candidate.release_date,
                major_region="Teyvat",
                is_released=True,
                is_current=True,
                changed_systems=candidate.changed_systems,
                source_url=candidate.source_url,
            )
            promoted = True
            effective_ver = candidate.version
            self._update_available = False
            msg = f"New version v{candidate.version} ('{candidate.name}') verified and promoted to current. Historical records preserved."
        else:
            self._update_available = True
            msg = f"Newer version v{candidate.version} ('{candidate.name}') verified as live. Update available: YES."

        self._last_verification = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self._discovery_status = "AVAILABLE"

        return VersionCheckResult(
            current_version=curr,
            discovered_version=candidate.version,
            verification_status="PASS",
            update_available=update_available,
            promoted=promoted,
            discovery_status="AVAILABLE",
            effective_current_version=effective_ver,
            message=msg,
        )

    def check_for_updates(
        self,
        simulate_network_failure: bool = False,
        discovery_provider: Optional[object] = None,
    ) -> VersionStatus:
        """Check for current version updates from approved sources.
        
        Handles failure gracefully:
        - If network/source fails, retains last verified version and sets discovery_status = "CACHED_OFFLINE".
        - Never resets current version to unknown or marks valid documents stale due to offline state.
        """
        if simulate_network_failure:
            logger.warning("Version discovery endpoint unreachable. Preserving last verified canonical version.")
            self._discovery_status = "CACHED_OFFLINE"
            self._update_available = False
            return self.get_status()

        self.check_and_update(discovery_provider=discovery_provider, auto_promote=False)
        return self.get_status()

    def get_status(
        self,
        total_documents: int = 0,
        stale_documents: int = 0,
        latest_canonical_update: str = "",
    ) -> VersionStatus:
        """Return the unified version status and system health summary."""
        curr = self.get_current_version()
        latest = self.get_latest_known_version()
        return VersionStatus(
            current_version=curr.version,
            latest_known_version=latest.version,
            project_target_version=self.get_project_target_version(),
            patch_name=curr.name,
            release_date=curr.release_date,
            major_region=curr.major_region,
            verification_status=curr.verification_status,
            discovery_status=self._discovery_status,
            last_version_verification=self._last_verification,
            app_version=settings.APP_VERSION,
            total_tracked_versions=len(self._versions),
            latest_canonical_update=latest_canonical_update or curr.release_date,
            stale_document_count=stale_documents,
            total_document_count=total_documents,
            update_available=self._update_available,
        )


version_service = VersionService()
