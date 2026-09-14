"""
GenshinIQ — Version Delta Engine & Delta-Driven Update Service.
Compares previous complete version against candidate version to compute fine-grained entity
and attribute diffs, determining the exact subset of knowledge documents requiring acquisition.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AttributeDiff(BaseModel):
    """Specific field modification on an entity."""
    field_name: str
    old_value: Any
    new_value: Any
    is_breaking: bool = False


class EntityDiffItem(BaseModel):
    """A modified or added entity between version snapshots."""
    entity_type: str  # character, weapon, artifact, quest, event, enemy, mechanic
    entity_id: str
    entity_name: str
    change_type: str  # added, modified, removed
    attribute_diffs: List[AttributeDiff] = Field(default_factory=list)


class DetailedVersionDelta(BaseModel):
    """Comprehensive diff comparing base_version to candidate_version."""
    base_version: str
    candidate_version: str
    computed_at: str
    new_characters: List[str] = Field(default_factory=list)
    modified_characters: List[str] = Field(default_factory=list)
    removed_characters: List[str] = Field(default_factory=list)
    new_weapons: List[str] = Field(default_factory=list)
    modified_weapons: List[str] = Field(default_factory=list)
    new_artifacts: List[str] = Field(default_factory=list)
    new_quests: List[str] = Field(default_factory=list)
    new_events: List[str] = Field(default_factory=list)
    new_enemies: List[str] = Field(default_factory=list)
    new_mechanics: List[str] = Field(default_factory=list)
    total_added: int = 0
    total_modified: int = 0
    total_removed: int = 0
    items: List[EntityDiffItem] = Field(default_factory=list)


class RequiredKnowledgeDelta(BaseModel):
    """Specific delta of knowledge documents that must be acquired for the new version."""
    candidate_version: str
    characters_requiring_guides: List[str] = Field(default_factory=list)
    weapons_requiring_metadata: List[str] = Field(default_factory=list)
    artifacts_requiring_guides: List[str] = Field(default_factory=list)
    mechanics_requiring_updates: List[str] = Field(default_factory=list)
    unaffected_knowledge_count: int = 0
    requires_official_patch_notes: bool = True


class VersionDeltaService:
    """Computes version deltas and drives delta-based knowledge acquisition."""

    def __init__(self, data_root: Optional[Path] = None):
        self.data_root = data_root or Path("data")
        self.processed_dir = self.data_root / "processed" / "game_data"

    def compare_version_datasets(
        self,
        base_version: str,
        candidate_version: str,
        base_characters: Dict[str, Any],
        candidate_characters: Dict[str, Any],
        base_weapons: Optional[Dict[str, Any]] = None,
        candidate_weapons: Optional[Dict[str, Any]] = None,
        base_artifacts: Optional[Dict[str, Any]] = None,
        candidate_artifacts: Optional[Dict[str, Any]] = None,
    ) -> DetailedVersionDelta:
        """Compute exact entity-level and stat-level delta between base and candidate."""
        items: List[EntityDiffItem] = []
        new_chars: List[str] = []
        mod_chars: List[str] = []
        rem_chars: List[str] = []

        base_weapons = base_weapons or {}
        candidate_weapons = candidate_weapons or {}
        base_artifacts = base_artifacts or {}
        candidate_artifacts = candidate_artifacts or {}

        # 1. Characters Diff
        base_char_ids = set(base_characters.keys())
        cand_char_ids = set(candidate_characters.keys())

        for cid in cand_char_ids - base_char_ids:
            c = candidate_characters[cid]
            cname = c.get("name", cid)
            new_chars.append(cname)
            items.append(
                EntityDiffItem(
                    entity_type="character",
                    entity_id=cid,
                    entity_name=cname,
                    change_type="added",
                )
            )

        for cid in base_char_ids - cand_char_ids:
            c = base_characters[cid]
            cname = c.get("name", cid)
            rem_chars.append(cname)
            items.append(
                EntityDiffItem(
                    entity_type="character",
                    entity_id=cid,
                    entity_name=cname,
                    change_type="removed",
                )
            )

        for cid in base_char_ids & cand_char_ids:
            b_char = base_characters[cid]
            c_char = candidate_characters[cid]
            cname = c_char.get("name", cid)
            attr_diffs = []

            # Check stats
            b_hp = b_char.get("base_hp_lvl90") or b_char.get("base_stats", {}).get("hp")
            c_hp = c_char.get("base_hp_lvl90") or c_char.get("base_stats", {}).get("hp")
            if b_hp and c_hp and b_hp != c_hp:
                attr_diffs.append(AttributeDiff(field_name="base_hp_lvl90", old_value=b_hp, new_value=c_hp))

            b_atk = b_char.get("base_atk_lvl90") or b_char.get("base_stats", {}).get("atk")
            c_atk = c_char.get("base_atk_lvl90") or c_char.get("base_stats", {}).get("atk")
            if b_atk and c_atk and b_atk != c_atk:
                attr_diffs.append(AttributeDiff(field_name="base_atk_lvl90", old_value=b_atk, new_value=c_atk))

            if attr_diffs:
                mod_chars.append(cname)
                items.append(
                    EntityDiffItem(
                        entity_type="character",
                        entity_id=cid,
                        entity_name=cname,
                        change_type="modified",
                        attribute_diffs=attr_diffs,
                    )
                )

        # 2. Weapons Diff
        new_weaps: List[str] = []
        mod_weaps: List[str] = []
        base_weap_ids = set(base_weapons.keys())
        cand_weap_ids = set(candidate_weapons.keys())

        for wid in cand_weap_ids - base_weap_ids:
            w = candidate_weapons[wid]
            wname = w.get("name", wid)
            new_weaps.append(wname)
            items.append(
                EntityDiffItem(
                    entity_type="weapon",
                    entity_id=wid,
                    entity_name=wname,
                    change_type="added",
                )
            )

        for wid in base_weap_ids & cand_weap_ids:
            b_w = base_weapons[wid]
            c_w = candidate_weapons[wid]
            wname = c_w.get("name", wid)
            if b_w.get("passive_desc") != c_w.get("passive_desc"):
                mod_weaps.append(wname)
                items.append(
                    EntityDiffItem(
                        entity_type="weapon",
                        entity_id=wid,
                        entity_name=wname,
                        change_type="modified",
                        attribute_diffs=[
                            AttributeDiff(
                                field_name="passive_desc",
                                old_value=b_w.get("passive_desc"),
                                new_value=c_w.get("passive_desc"),
                            )
                        ],
                    )
                )

        # 3. Artifacts Diff
        new_arts: List[str] = []
        base_art_ids = set(base_artifacts.keys())
        cand_art_ids = set(candidate_artifacts.keys())

        for aid in cand_art_ids - base_art_ids:
            a = candidate_artifacts[aid]
            aname = a.get("name", aid)
            new_arts.append(aname)
            items.append(
                EntityDiffItem(
                    entity_type="artifact",
                    entity_id=aid,
                    entity_name=aname,
                    change_type="added",
                )
            )

        return DetailedVersionDelta(
            base_version=base_version,
            candidate_version=candidate_version,
            computed_at=datetime.now(timezone.utc).isoformat(),
            new_characters=new_chars,
            modified_characters=mod_chars,
            removed_characters=rem_chars,
            new_weapons=new_weaps,
            modified_weapons=mod_weaps,
            new_artifacts=new_arts,
            total_added=len(new_chars) + len(new_weaps) + len(new_arts),
            total_modified=len(mod_chars) + len(mod_weaps),
            total_removed=len(rem_chars),
            items=items,
        )

    def compute_knowledge_delta(
        self,
        delta: DetailedVersionDelta,
        existing_knowledge_doc_count: int,
    ) -> RequiredKnowledgeDelta:
        """
        Determines the exact targeted set of knowledge required for candidate_version.
        Unaffected existing knowledge documents are preserved without unnecessary rebuilds.
        """
        chars_needed = list(delta.new_characters) + list(delta.modified_characters)
        weaps_needed = list(delta.new_weapons)
        arts_needed = list(delta.new_artifacts)

        return RequiredKnowledgeDelta(
            candidate_version=delta.candidate_version,
            characters_requiring_guides=chars_needed,
            weapons_requiring_metadata=weaps_needed,
            artifacts_requiring_guides=arts_needed,
            mechanics_requiring_updates=[],
            unaffected_knowledge_count=existing_knowledge_doc_count,
            requires_official_patch_notes=True,
        )


version_delta_service = VersionDeltaService()
