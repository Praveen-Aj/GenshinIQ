"""
KQM Theorycrafting Library (TCL) Source Adapter.
Handles discovery, acquisition, normalization, and validation of peer-reviewed combat mechanics.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter
from backend.models.knowledge import compute_content_hash

logger = logging.getLogger(__name__)


class TCLAdapter(SourceAdapter):
    """Peer-reviewed combat mechanics and evidence repository adapter."""

    def __init__(self, base_url: str = "https://library.keqingmains.com"):
        super().__init__(
            source_id="src_kqm_tcl",
            domains=["game_mechanics_knowledge", "theorycrafting_knowledge"],
            authority_tier=2,
        )
        self.base_url = base_url

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        """Discover available TCL mechanic documents from local knowledge."""
        discovered: List[AdapterDiscoveredItem] = []
        local_dir = Path("data/knowledge")
        if local_dir.exists():
            for f in local_dir.glob("mechanics_*.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        doc = json.load(jf)
                    meta = doc.get("metadata", {})
                    discovered.append(
                        AdapterDiscoveredItem(
                            source_id=self.source_id,
                            target_version=meta.get("game_version", "7.0"),
                            entity_type="game_mechanic",
                            identifier=f.stem,
                            title_or_name=doc.get("title", f.stem),
                            uri_or_url=meta.get("source_url", f"{self.base_url}/combat-mechanics/{f.stem}"),
                            retrieved_at=meta.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                            raw_metadata={"file_path": str(f)},
                        )
                    )
                except Exception as e:
                    logger.debug(f"Failed to inspect TCL mechanic {f}: {e}")
        return discovered

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        fpath = item.raw_metadata.get("file_path")
        if fpath and Path(fpath).exists():
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "title": item.title_or_name,
            "url": item.uri_or_url,
            "version": item.target_version,
            "fetched_at": item.retrieved_at,
        }

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": raw_payload.get("id"),
            "title": raw_payload.get("title"),
            "metadata": raw_payload.get("metadata", {}),
            "summary": raw_payload.get("summary", ""),
            "content": raw_payload.get("content", ""),
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        meta = parsed_data.get("metadata", {})
        meta["source_id"] = self.source_id
        meta["authority_tier"] = self.authority_tier
        meta["game_version"] = target_version
        meta["content_hash"] = compute_content_hash(str(parsed_data.get("content", "")))
        return {
            "id": parsed_data.get("id"),
            "title": parsed_data.get("title"),
            "metadata": meta,
            "summary": parsed_data.get("summary"),
            "content": parsed_data.get("content"),
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        errors: List[str] = []
        if not normalized_data.get("id"):
            errors.append("Missing mechanic document ID")
        content = str(normalized_data.get("content", ""))
        if len(content) < 20:
            errors.append("Mechanic content is too short or empty")

        return AdapterValidationResult(
            is_valid=len(errors) == 0,
            source_id=self.source_id,
            target_version=normalized_data.get("metadata", {}).get("game_version", "7.0"),
            entity_count=1 if len(errors) == 0 else 0,
            errors=errors,
        )
