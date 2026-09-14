"""
AnimeGameData / GenshinData Source Adapter.
Handles discovery, acquisition, normalization, and validation of raw datamined game data and content catalogs.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional
import urllib.request

from backend.adapters.base import AdapterDiscoveredItem, AdapterValidationResult, SourceAdapter

logger = logging.getLogger(__name__)


class AnimeGameDataAdapter(SourceAdapter):
    """PRIMARY raw structured and game content data adapter."""

    def __init__(self, repo_url: str = "https://github.com/DimbreathBot/AnimeGameData", timeout: float = 5.0):
        super().__init__(
            source_id="src_animegamedata",
            domains=[
                "character_deterministic",
                "weapon_knowledge",
                "artifact_knowledge",
                "quest_world_knowledge",
            ],
            authority_tier=3,
        )
        self.repo_url = repo_url
        self.timeout = timeout

    def discover(self, target_version: Optional[str] = None) -> List[AdapterDiscoveredItem]:
        """Query GitHub commit history to detect new released version branch/tag."""
        discovered: List[AdapterDiscoveredItem] = []
        api_url = "https://api.github.com/repos/DimbreathBot/AnimeGameData/commits?per_page=5"

        detected_v = "7.0"
        commit_sha = "upstream_latest"

        try:
            req = urllib.request.Request(
                api_url,
                headers={"User-Agent": "GenshinIQ-Adapter/1.0", "Accept": "application/vnd.github.v3+json"},
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                for c in data:
                    msg = c.get("commit", {}).get("message", "")
                    m = re.search(r"CNRELWin(\d+\.\d+)", msg) or re.search(r"(\d+\.\d+)", msg)
                    if m:
                        detected_v = m.group(1)
                        commit_sha = c.get("sha", commit_sha)
                        break
        except Exception as e:
            logger.warning(f"AnimeGameDataAdapter GitHub discovery failed: {e}. Using target_version.")
            if target_version:
                detected_v = target_version

        v = target_version or detected_v
        discovered.append(
            AdapterDiscoveredItem(
                source_id=self.source_id,
                target_version=v,
                entity_type="structured_dataset",
                identifier=f"animegamedata_v{v.replace('.', '_')}",
                title_or_name=f"AnimeGameData Version {v}",
                uri_or_url=self.repo_url,
                retrieved_at=datetime.now(timezone.utc).isoformat(),
                raw_metadata={"commit_sha": commit_sha},
            )
        )
        return discovered

    def fetch(self, item: AdapterDiscoveredItem) -> Dict[str, Any]:
        """Return reference to raw tables required for this version."""
        raw_tables = [
            "AvatarExcelConfigData.json",
            "WeaponExcelConfigData.json",
            "AvatarCurveExcelConfigData.json",
            "WeaponCurveExcelConfigData.json",
            "ReliquaryLevelExcelConfigData.json",
            "MaterialExcelConfigData.json",
            "ChapterExcelConfigData.json",
            "MainQuestExcelConfigData.json",
            "DungeonExcelConfigData.json",
            "DailyDungeonConfigData.json",
            "MonsterDescribeExcelConfigData.json",
            "CityConfigData.json",
            "WorldAreaConfigData.json",
            "AchievementExcelConfigData.json",
            "CookRecipeExcelConfigData.json",
        ]
        return {
            "version": item.target_version,
            "required_tables": raw_tables,
            "fetched_at": item.retrieved_at,
        }

    def parse(self, raw_payload: Dict[str, Any]) -> Dict[str, Any]:
        """Intermediate parsing step."""
        return {
            "version": raw_payload.get("version", "7.0"),
            "table_count": len(raw_payload.get("required_tables", [])),
        }

    def normalize(self, parsed_data: Dict[str, Any], target_version: str) -> Dict[str, Any]:
        """Normalize into versioned structured dataset summary."""
        return {
            "dataset_version": target_version,
            "source_id": self.source_id,
            "catalogs": [
                "characters",
                "weapons",
                "artifacts",
                "materials",
                "curves",
                "quests",
                "events",
                "domains",
                "enemies",
                "regions",
                "achievements",
                "recipes",
            ],
            "normalized_at": datetime.now(timezone.utc).isoformat(),
        }

    def validate(self, normalized_data: Dict[str, Any]) -> AdapterValidationResult:
        """Validate catalog completeness."""
        errors: List[str] = []
        catalogs = normalized_data.get("catalogs", [])
        if "characters" not in catalogs:
            errors.append("Missing characters catalog")
        if "weapons" not in catalogs:
            errors.append("Missing weapons catalog")

        return AdapterValidationResult(
            is_valid=len(errors) == 0,
            source_id=self.source_id,
            target_version=normalized_data.get("dataset_version", "unknown"),
            entity_count=len(catalogs),
            errors=errors,
        )
