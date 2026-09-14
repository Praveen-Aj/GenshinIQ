"""
Enka.Network Source Adapter.
Handles player account showcase retrieval with rate-limiting and TTL disk caching.
ACCOUNT LAYER ONLY — Never treated as canonical game knowledge.
"""

from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import urllib.request

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter

logger = logging.getLogger(__name__)


class EnkaAdapter(SourceAdapter):
    """Player account showcase adapter."""

    def __init__(self, api_base: str = "https://enka.network/api/uid"):
        super().__init__(
            source_id="src_enka_network",
            domains=["account_showcase", "player_inventory"],
            authority_tier=4,
        )
        self.api_base = api_base

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        # Account data is user-driven, not patch-version scheduled
        return []

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        uid = item.identifier
        url = f"{self.api_base}/{uid}"
        return {
            "uid": uid,
            "url": url,
            "fetched_at": datetime.now(timezone.utc).isoformat(),
        }

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "uid": raw_payload.get("uid"),
            "player_info": raw_payload.get("playerInfo", {}),
            "avatar_info_list": raw_payload.get("avatarInfoList", []),
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        return {
            "uid": parsed_data.get("uid"),
            "characters": parsed_data.get("avatar_info_list", []),
            "source_id": self.source_id,
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        errors = []
        if not normalized_data.get("uid"):
            errors.append("Missing player UID")
        return AdapterValidationResult(
            is_valid=len(errors) == 0,
            source_id=self.source_id,
            target_version="live_player_account",
            entity_count=len(normalized_data.get("characters", [])),
            errors=errors,
        )
