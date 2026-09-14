"""
KeqingMains (KQM) Source Adapter.
Handles discovery, acquisition, parsing, normalization, and validation of curated character guides and theorycrafting.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import urllib.request

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter
from backend.models.knowledge import compute_content_hash

logger = logging.getLogger(__name__)


class KQMAdapter(SourceAdapter):
    """Primary curated theorycrafting and character guide adapter."""

    def __init__(self, base_url: str = "https://keqingmains.com", timeout: float = 5.0):
        super().__init__(
            source_id="src_kqm_guides",
            domains=["character_knowledge", "team_building_knowledge", "theorycrafting_knowledge"],
            authority_tier=2,
        )
        self.base_url = base_url
        self.timeout = timeout

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        """Discover available KQM guides by inspecting local directory or online sitemap."""
        discovered: List[AdapterDiscoveredItem] = []
        # Check existing verified local KQM guides
        local_kqm_dir = Path("data/knowledge")
        if local_kqm_dir.exists():
            for f in local_kqm_dir.glob("kqm_*_guide.json"):
                try:
                    with open(f, "r", encoding="utf-8") as jf:
                        doc = json.load(jf)
                    meta = doc.get("metadata", {})
                    cname = meta.get("character") or f.stem.replace("kqm_", "").replace("_guide", "")
                    doc_ver = meta.get("game_version", "7.0")
                    discovered.append(
                        AdapterDiscoveredItem(
                            source_id=self.source_id,
                            target_version=doc_ver,
                            entity_type="character_guide",
                            identifier=f.stem,
                            title_or_name=doc.get("title", f"KQM {cname} Guide"),
                            uri_or_url=meta.get("source_url", f"{self.base_url}/{cname.lower().replace(' ', '-')}/"),
                            retrieved_at=meta.get("retrieved_at", datetime.now(timezone.utc).isoformat()),
                            raw_metadata={"character": cname, "file_path": str(f)},
                        )
                    )
                except Exception as e:
                    logger.debug(f"Failed to inspect local KQM guide {f}: {e}")
        return discovered

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        """Fetch raw guide payload."""
        fpath = item.raw_metadata.get("file_path")
        if fpath and Path(fpath).exists():
            with open(fpath, "r", encoding="utf-8") as f:
                return json.load(f)
        return {
            "title": item.title_or_name,
            "character": item.raw_metadata.get("character"),
            "url": item.uri_or_url,
            "version": item.target_version,
            "fetched_at": item.retrieved_at,
        }

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract structured build priorities and rotation details."""
        return {
            "id": raw_payload.get("id"),
            "title": raw_payload.get("title"),
            "metadata": raw_payload.get("metadata", {}),
            "summary": raw_payload.get("summary", ""),
            "content": raw_payload.get("content", ""),
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        """Ensure full KnowledgeDocument schema compliance."""
        meta = parsed_data.get("metadata", {})
        meta["source_id"] = self.source_id
        meta["authority_tier"] = self.authority_tier
        meta["game_version"] = target_version
        content = parsed_data.get("content", "")
        meta["content_hash"] = compute_content_hash(content if isinstance(content, str) else json.dumps(content))
        return {
            "id": parsed_data.get("id"),
            "title": parsed_data.get("title"),
            "metadata": meta,
            "summary": parsed_data.get("summary"),
            "content": content,
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        """Validate that guide has required sections without placeholders."""
        errors: List[str] = []
        content = str(normalized_data.get("content", ""))
        for placeholder in ["placeholder", "to be determined", "data unavailable"]:
            if placeholder in content.lower():
                errors.append(f"Forbidden placeholder '{placeholder}' found in guide content")

        meta = normalized_data.get("metadata", {})
        if not meta.get("character"):
            errors.append("Missing character target in guide metadata")

        return AdapterValidationResult(
            is_valid=len(errors) == 0,
            source_id=self.source_id,
            target_version=meta.get("game_version", "7.0"),
            entity_count=1 if len(errors) == 0 else 0,
            errors=errors,
        )
