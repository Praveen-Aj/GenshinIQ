"""
Service for version-driven character release classification and knowledge applicability.
Enforces the boundary between live playable characters and unreleased client preview entities.
Dynamically transitions release status as game versions advance without hardcoding character names.
"""

import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from backend.models.character_knowledge_package import (
    CharacterReleaseStatus,
    FieldQualityClassification,
)
from backend.services.version_service import parse_version_tuple

logger = logging.getLogger(__name__)

# Default live playable cutoff version in the active dataset
# Real-world playable Genshin Impact version with live character banners
DEFAULT_LIVE_PLAYABLE_VERSION = "5.4"


class CharacterReleaseService:
    """Classifies character release status based on version history and official evidence."""

    def __init__(self, live_playable_version: str = DEFAULT_LIVE_PLAYABLE_VERSION):
        self.live_playable_version = live_playable_version

    def classify_character(
        self,
        char_data: Dict[str, Any],
        live_version: Optional[str] = None,
    ) -> CharacterReleaseStatus:
        """
        Classify a character's release status based on canonical version data.
        
        Rules:
        1. If game_version_introduced is missing/invalid -> UNKNOWN
        2. If parse_version_tuple(game_version_introduced) <= parse_version_tuple(effective_live_version):
           -> Character is LIVE_RELEASED (playable in the live game).
        3. If parse_version_tuple(game_version_introduced) > parse_version_tuple(effective_live_version):
           - Check if confirmed in official promotional material/trailer (e.g. next minor patch):
             -> UPCOMING_CONFIRMED
           - Otherwise:
             -> UNRELEASED_PREVIEW (client binary entity or future roadmap)
        """
        effective_live = live_version or self.live_playable_version
        intro_ver = str(char_data.get("game_version_introduced", "")).strip()

        if not intro_ver:
            return CharacterReleaseStatus.UNKNOWN

        intro_tuple = parse_version_tuple(intro_ver)
        live_tuple = parse_version_tuple(effective_live)

        if intro_tuple == (0, 0):
            return CharacterReleaseStatus.UNKNOWN

        if intro_tuple <= live_tuple:
            return CharacterReleaseStatus.LIVE_RELEASED

        # Characters scheduled for the immediate next patch or with official trailer preview
        # e.g., if live is 5.4 and intro is 5.5, or explicit upcoming flag
        is_immediate_next = (
            intro_tuple[0] == live_tuple[0] and intro_tuple[1] == live_tuple[1] + 1
        )
        if is_immediate_next or char_data.get("is_upcoming_confirmed"):
            return CharacterReleaseStatus.UPCOMING_CONFIRMED

        return CharacterReleaseStatus.UNRELEASED_PREVIEW

    def get_applicability_requirements(
        self, release_status: CharacterReleaseStatus
    ) -> Dict[str, str]:
        """
        Return the applicable knowledge contract requirements for a release status.
        
        - LIVE_RELEASED:
            structured_data: REQUIRED
            mechanics: REQUIRED
            expert_guide: REQUIRED (or TRACKED_GAP if community guide unwritten)
        - UPCOMING_CONFIRMED:
            structured_data: APPLICABLE (if in client data)
            mechanics: PREVIEW_ONLY
            expert_guide: NOT_APPLICABLE
        - UNRELEASED_PREVIEW:
            structured_data: APPLICABLE (if in client data)
            mechanics: PREVIEW_ONLY
            expert_guide: NOT_APPLICABLE
        - UNKNOWN:
            all: UNKNOWN
        """
        if release_status == CharacterReleaseStatus.LIVE_RELEASED:
            return {
                "structured_data": "REQUIRED",
                "mechanics": "REQUIRED",
                "expert_guide": "REQUIRED",
                "applicability_reason": "Live playable character in current active game version",
            }
        elif release_status in (
            CharacterReleaseStatus.UPCOMING_CONFIRMED,
            CharacterReleaseStatus.UNRELEASED_PREVIEW,
        ):
            reason = (
                "Upcoming confirmed character; community guides not applicable prior to live release"
                if release_status == CharacterReleaseStatus.UPCOMING_CONFIRMED
                else "Unreleased client preview entity; live guides and meta rotations not applicable"
            )
            return {
                "structured_data": "APPLICABLE",
                "mechanics": "PREVIEW_ONLY",
                "expert_guide": "NOT_APPLICABLE",
                "applicability_reason": reason,
            }
        else:
            return {
                "structured_data": "UNKNOWN",
                "mechanics": "UNKNOWN",
                "expert_guide": "UNKNOWN",
                "applicability_reason": "Unknown character version status",
            }

    def partition_characters(
        self,
        characters: List[Dict[str, Any]],
        live_version: Optional[str] = None,
    ) -> Dict[CharacterReleaseStatus, List[Dict[str, Any]]]:
        """Group characters into LIVE_RELEASED, UPCOMING_CONFIRMED, UNRELEASED_PREVIEW, UNKNOWN."""
        partitions: Dict[CharacterReleaseStatus, List[Dict[str, Any]]] = {
            CharacterReleaseStatus.LIVE_RELEASED: [],
            CharacterReleaseStatus.UPCOMING_CONFIRMED: [],
            CharacterReleaseStatus.UNRELEASED_PREVIEW: [],
            CharacterReleaseStatus.UNKNOWN: [],
        }
        for c in characters:
            status = self.classify_character(c, live_version)
            partitions[status].append(c)
        return partitions


# Global singleton
character_release_service = CharacterReleaseService()
