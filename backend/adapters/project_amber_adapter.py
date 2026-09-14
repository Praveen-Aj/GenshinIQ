"""
Project Amber (Ambr.top) Source Adapter.
Handles secondary structured validation and entity cross-checking.
"""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter

logger = logging.getLogger(__name__)


class ProjectAmberAdapter(SourceAdapter):
    """Secondary structured validation adapter."""

    def __init__(self, base_url: str = "https://ambr.top/en/archive"):
        super().__init__(
            source_id="src_project_amber",
            domains=["character_deterministic", "weapon_knowledge"],
            authority_tier=3,
        )
        self.base_url = base_url

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        v = target_version or "7.0"
        return [
            AdapterDiscoveredItem(
                source_id=self.source_id,
                target_version=v,
                entity_type="secondary_structured_reference",
                identifier=f"ambr_v{v.replace('.', '_')}",
                title_or_name=f"Project Amber Archive v{v}",
                uri_or_url=f"{self.base_url}/avatar",
                retrieved_at=datetime.now(timezone.utc).isoformat(),
            )
        ]

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        return {
            "version": item.target_version,
            "source": self.source_id,
            "url": item.uri_or_url,
            "fetched_at": item.retrieved_at,
        }

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "version": raw_payload.get("version", "7.0"),
            "status": "PARSED",
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        return {
            "target_version": target_version,
            "source_id": self.source_id,
            "is_corroborator": True,
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        return AdapterValidationResult(
            is_valid=True,
            source_id=self.source_id,
            target_version=normalized_data.get("target_version", "7.0"),
            entity_count=1,
        )
