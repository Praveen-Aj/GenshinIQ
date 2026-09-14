"""
Genshin Open Object Description (GOOD) Source Adapter.
Handles parsing and normalization of player inventory exports (Genshin Optimizer format).
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter

logger = logging.getLogger(__name__)


class GOODAdapter(SourceAdapter):
    """Genshin Optimizer GOOD format import adapter."""

    def __init__(self):
        super().__init__(
            source_id="src_genshin_optimizer",
            domains=["account_inventory", "artifact_inventory"],
            authority_tier=2,
        )

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        # Driven by file upload or manual paste, not web crawling
        return []

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        return item.raw_metadata

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "format": raw_payload.get("format", "GOOD"),
            "version": raw_payload.get("version", 1),
            "characters": raw_payload.get("characters", []),
            "artifacts": raw_payload.get("artifacts", []),
            "weapons": raw_payload.get("weapons", []),
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "format": parsed_data.get("format"),
            "character_count": len(parsed_data.get("characters", [])),
            "artifact_count": len(parsed_data.get("artifacts", [])),
            "weapon_count": len(parsed_data.get("weapons", [])),
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        errors = []
        if normalized_data.get("format") != "GOOD":
            errors.append("Invalid format: payload is not a valid GOOD schema export")
        return AdapterValidationResult(
            is_valid=len(errors) == 0,
            source_id=self.source_id,
            target_version="good_export",
            entity_count=normalized_data.get("character_count", 0),
            errors=errors,
        )
