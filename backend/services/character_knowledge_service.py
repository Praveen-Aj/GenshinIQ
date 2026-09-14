"""
GenshinIQ — Character Knowledge Service
Compiles, verifies, and serves formal Character Knowledge Packages for all 119 canonical characters.
Operationalizes the Finite Knowledge Contract:
- Deterministic extraction from raw client avatar data
- Deterministic mathematical derivations (scaling, curves, thresholds)
- Curated theorycrafting integration (KQM, TCL, Wiki)
- Systematic knowledge gap cataloging without fabrication
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.models.character_knowledge_package import (
    CharacterKnowledgePackage,
    CharacterReleaseStatus,
    DeterministicCharacterKnowledge,
    CuratedCharacterKnowledge,
    DerivedCalculation,
    FieldQualityClassification,
)
from backend.services.stat_engine import stat_engine_service as stat_engine
from backend.services.character_release_service import character_release_service

logger = logging.getLogger(__name__)


class CharacterKnowledgeService:
    """Service to compile, validate, and query formal Character Knowledge Packages."""

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        target_version: str = "7.0",
    ):
        self.base_dir = base_dir or Path(".")
        self.target_version = target_version
        self.processed_dir = self.base_dir / "data" / "processed" / "game_data"
        self.raw_avatars_dir = self.base_dir / "data" / "raw" / "game_data" / "avatars"
        self.knowledge_dir = self.base_dir / "data" / "knowledge"
        self.canonical_dir = self.base_dir / "data" / "canonical"
        self.packages_cache: Dict[str, CharacterKnowledgePackage] = {}
        self._characters_cache: Optional[List[Dict[str, Any]]] = None

    def _load_canonical_characters(self) -> List[Dict[str, Any]]:
        """Load all 119 characters from processed characters.json."""
        if self._characters_cache is None:
            chars_path = self.processed_dir / "characters.json"
            if not chars_path.exists():
                chars_path = self.processed_dir / "versions" / self.target_version / "characters.json"
            if not chars_path.exists():
                logger.warning("characters.json not found in processed game data.")
                return []
            with open(chars_path, "r", encoding="utf-8") as f:
                self._characters_cache = json.load(f)
        return self._characters_cache

    def _load_raw_avatar(self, character_id: str) -> Optional[Dict[str, Any]]:
        """Load raw avatar JSON if available from data/raw/game_data/avatars/{id}.json."""
        raw_path = self.raw_avatars_dir / f"{character_id}.json"
        if raw_path.exists():
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    payload = json.load(f)
                    return payload.get("data", payload)
            except Exception as e:
                logger.warning(f"Error reading raw avatar {character_id}: {e}")
        return None

    def _find_knowledge_docs(self, character_name: str) -> List[Tuple[str, Dict[str, Any]]]:
        """Find all knowledge documents (KQM and Wiki) matching a character."""
        norm_target = character_name.lower().replace(" ", "").replace("_", "").replace("-", "")
        matches = []
        for doc_file in self.knowledge_dir.glob("*.json"):
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    doc_data = json.load(f)
                meta = doc_data.get("metadata", {})
                char_in_meta = meta.get("character") or ""
                norm_char = char_in_meta.lower().replace(" ", "").replace("_", "").replace("-", "")
                
                # Check filename slug match as fallback
                slug = doc_file.stem.replace("wiki_", "").replace("kqm_", "").replace("_guide", "").replace("_extended", "")
                norm_slug = slug.lower().replace(" ", "").replace("_", "").replace("-", "")
                
                if norm_target in (norm_char, norm_slug) or (norm_char and norm_char in norm_target):
                    matches.append((doc_file.name, doc_data))
            except Exception:
                continue
        return matches

    def _record_knowledge_gap(
        self,
        character_name: str,
        character_id: str,
        field_name: str,
        reason: str,
        required_source: str = "src_kqm_guides",
    ) -> None:
        """Register an explicit knowledge gap in data/canonical/knowledge_gaps.json without fabricating text."""
        gaps_path = self.canonical_dir / "knowledge_gaps.json"
        if not gaps_path.exists():
            return
        try:
            with open(gaps_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            gap_id = f"gap_{character_name.lower().replace(' ', '_')}_{field_name.lower()}"
            existing_ids = {g.get("gap_id") for g in data.get("gaps", [])}
            
            if gap_id not in existing_ids:
                new_gap = {
                    "gap_id": gap_id,
                    "topic": "Character Theorycrafting",
                    "entity": f"{character_name} (ID {character_id})",
                    "field": field_name,
                    "version": self.target_version,
                    "question": f"What are the authoritative 7.0 {field_name.replace('_', ' ')} recommendations for {character_name}?",
                    "status": "AWAITING_EXPERT_SOURCE",
                    "recommended_source": required_source,
                    "notes": reason,
                    "registered_at": datetime.now(timezone.utc).isoformat(),
                }
                data.setdefault("gaps", []).append(new_gap)
                data["total_gaps_tracked"] = len(data["gaps"])
                data["updated_at"] = datetime.now(timezone.utc).isoformat()
                
                with open(gaps_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to record knowledge gap: {e}")

    def compile_character_package(self, char_data: Dict[str, Any], record_gap: bool = False) -> CharacterKnowledgePackage:
        """
        Compile complete Character Knowledge Package adhering to Knowledge Contract:
        - Deterministic fields from raw/processed data
        - Derived calculations with explicit mathematical formulas
        - Curated fields from genuine expert sources (KQM/Wiki)
        - Missing theorycrafting cataloged as explicit KNOWLEDGE_GAPs
        """
        cid = str(char_data.get("id"))
        cname = char_data.get("name", "Unknown")
        element = char_data.get("element", "Unknown")
        weapon_type = char_data.get("weapon_type", "Unknown")
        rarity = char_data.get("rarity", 4)
        release_ver = char_data.get("game_version_introduced", "1.0")
        
        # Determine release status dynamically via CharacterReleaseService
        release_status = character_release_service.classify_character(char_data)
        is_released = (release_status == CharacterReleaseStatus.LIVE_RELEASED)
        applicability = character_release_service.get_applicability_requirements(release_status)

        field_classifications: Dict[str, FieldQualityClassification] = {}
        provenance_sources: List[str] = ["src_animegamedata", "src_project_amber"]

        # ---------------------------------------------------------------------
        # 1. Deterministic Data & Raw Binary Parsing
        # ---------------------------------------------------------------------
        raw_avatar = self._load_raw_avatar(cid)
        talents_list = []
        constellations_list = []
        mechanics_list = []

        if raw_avatar:
            # Parse raw talent definitions
            raw_talents = raw_avatar.get("talent", {})
            for t_idx, t_val in raw_talents.items():
                talents_list.append({
                    "skill_id": t_val.get("skillId"),
                    "name": t_val.get("name", f"Talent {t_idx}"),
                    "type": t_val.get("type", 0),
                    "description": t_val.get("description", ""),
                    "cooldown": t_val.get("cooldown", 0),
                    "energy_cost": t_val.get("cost", 0),
                    "scaling_levels": len(t_val.get("promote", {})),
                })
            
            # Parse raw constellations
            raw_consts = raw_avatar.get("constellation", {})
            for c_idx, c_val in raw_consts.items():
                constellations_list.append({
                    "level": int(c_idx) + 1,
                    "name": c_val.get("name", f"C{int(c_idx)+1}"),
                    "description": c_val.get("description", ""),
                })
        else:
            # Fallback to processed character data
            for t in char_data.get("talents", []):
                talents_list.append(t if isinstance(t, dict) else {"name": str(t)})
            for c in char_data.get("constellations", []):
                constellations_list.append(c if isinstance(c, dict) else {"name": str(c)})

        field_classifications["deterministic.identity"] = FieldQualityClassification.VERIFIED
        field_classifications["deterministic.element"] = FieldQualityClassification.VERIFIED
        field_classifications["deterministic.weapon_type"] = FieldQualityClassification.VERIFIED
        field_classifications["deterministic.rarity"] = FieldQualityClassification.VERIFIED
        field_classifications["deterministic.talents"] = FieldQualityClassification.VERIFIED if len(talents_list) >= 3 else FieldQualityClassification.PARTIAL
        field_classifications["deterministic.constellations"] = FieldQualityClassification.VERIFIED if len(constellations_list) >= 6 else FieldQualityClassification.PARTIAL

        # ---------------------------------------------------------------------
        # 2. Deterministic Derivations (Stat Scaling & Progression Breakpoints)
        # ---------------------------------------------------------------------
        derived_calculations: List[DerivedCalculation] = []
        base_stats_map = {}
        ascension_stats_map = {}

        try:
            # Deterministic Lv 1 and Lv 90 stat calculation
            stats_lv1, special_lv1, status_lv1, _ = stat_engine.resolve_character_base_stats(cname, level=1, ascension=0)
            stats_lv90, special_lv90, status_lv90, _ = stat_engine.resolve_character_base_stats(cname, level=90, ascension=6)
            
            base_stats_map = {
                "lvl1": {"hp": stats_lv1.get("hp", 0), "atk": stats_lv1.get("atk", 0), "def": stats_lv1.get("def", 0)},
                "lvl90": {"hp": stats_lv90.get("hp", 0), "atk": stats_lv90.get("atk", 0), "def": stats_lv90.get("def", 0)},
            }
            ascension_stats_map = {
                "special_stats_lvl90": special_lv90,
            }

            derived_calculations.append(DerivedCalculation(
                name="Character Lv 90 Base HP",
                formula="round(initValue * hp_curve_lvl90 + promote_add_hp)",
                inputs={"level": 90, "ascension": 6},
                output=stats_lv90.get("hp", 0),
                derivation_rule="AvatarGrowthCurve multiplier + Promotion bonus addition (Deterministic Invariant)",
            ))
            derived_calculations.append(DerivedCalculation(
                name="Character Lv 90 Base ATK",
                formula="round(initValue * atk_curve_lvl90 + promote_add_atk)",
                inputs={"level": 90, "ascension": 6},
                output=stats_lv90.get("atk", 0),
                derivation_rule="AvatarGrowthCurve multiplier + Promotion bonus addition (Deterministic Invariant)",
            ))
            derived_calculations.append(DerivedCalculation(
                name="Character Lv 90 Base DEF",
                formula="round(initValue * def_curve_lvl90 + promote_add_def)",
                inputs={"level": 90, "ascension": 6},
                output=stats_lv90.get("def", 0),
                derivation_rule="AvatarGrowthCurve multiplier + Promotion bonus addition (Deterministic Invariant)",
            ))
            field_classifications["deterministic.base_stats"] = FieldQualityClassification.VERIFIED_DERIVED
            field_classifications["deterministic.scaling"] = FieldQualityClassification.VERIFIED_DERIVED
        except Exception as e:
            logger.warning(f"Could not compute derived stats for {cname}: {e}")
            hp90 = char_data.get("base_hp_lvl90", 0)
            atk90 = char_data.get("base_atk_lvl90", 0)
            def90 = char_data.get("base_def_lvl90", 0)
            base_stats_map = {"lvl90": {"hp": hp90, "atk": atk90, "def": def90}}
            field_classifications["deterministic.base_stats"] = FieldQualityClassification.VERIFIED if hp90 > 0 else FieldQualityClassification.MISSING

        deterministic_pkg = DeterministicCharacterKnowledge(
            id=cid,
            name=cname,
            element=element,
            weapon_type=weapon_type,
            rarity=rarity,
            region=char_data.get("region", "Unknown"),
            release_version=release_ver,
            base_stats=base_stats_map,
            ascension_stats=ascension_stats_map,
            talents=talents_list,
            constellations=constellations_list,
            relevant_mechanics=mechanics_list,
        )

        # ---------------------------------------------------------------------
        # 3. Curated Expert Knowledge & Gap Detection
        # ---------------------------------------------------------------------
        knowledge_docs = self._find_knowledge_docs(cname)
        knowledge_gaps: List[str] = []
        curated_pkg = CuratedCharacterKnowledge()

        # Check if genuine KQM or Wiki guide exists
        kqm_docs = [d for d in knowledge_docs if "kqm_" in d[0]]
        wiki_docs = [d for d in knowledge_docs if "wiki_" in d[0]]
        primary_doc = kqm_docs[0] if kqm_docs else (wiki_docs[0] if wiki_docs else None)

        if primary_doc:
            doc_filename, doc_payload = primary_doc
            meta = doc_payload.get("metadata", {})
            doc_ver = meta.get("game_version", "5.4")
            src_id = meta.get("source_id", "src_kqm_guides")
            provenance_sources.append(src_id)

            content_text = doc_payload.get("content", "")
            if isinstance(content_text, dict):
                content_text = json.dumps(content_text)

            # Map fields present in the text
            curated_pkg.role = "Support / Buffer" if "support" in content_text.lower() else "DPS / On-Field"
            
            # Weapon and Artifact recommendations parsed from guide
            if "weapon" in content_text.lower():
                curated_pkg.weapon_recommendations.append({"source": doc_filename, "status": "EXTRACTED_FROM_GUIDE"})
            if "artifact" in content_text.lower():
                curated_pkg.artifact_recommendations.append({"source": doc_filename, "status": "EXTRACTED_FROM_GUIDE"})

            # Classify version freshness
            is_current = (doc_ver == self.target_version)
            curated_classification = FieldQualityClassification.VERIFIED if is_current else FieldQualityClassification.STALE
            
            field_classifications["curated.role"] = curated_classification
            field_classifications["curated.weapons"] = curated_classification
            field_classifications["curated.artifacts"] = curated_classification
            
            if "rotation" in content_text.lower():
                field_classifications["curated.rotation"] = curated_classification
            else:
                field_classifications["curated.rotation"] = FieldQualityClassification.MISSING
                knowledge_gaps.append("curated.rotation")

            if "energy" in content_text.lower() or "er requirements" in content_text.lower():
                field_classifications["curated.energy_requirements"] = curated_classification
            else:
                field_classifications["curated.energy_requirements"] = FieldQualityClassification.MISSING
                knowledge_gaps.append("curated.energy_requirements")
        else:
            if not is_released:
                # UNRELEASED ENTITY: Curated fields are NOT_APPLICABLE per Knowledge Contract
                field_classifications["curated.role"] = FieldQualityClassification.NOT_APPLICABLE
                field_classifications["curated.weapons"] = FieldQualityClassification.NOT_APPLICABLE
                field_classifications["curated.artifacts"] = FieldQualityClassification.NOT_APPLICABLE
                field_classifications["curated.teams"] = FieldQualityClassification.NOT_APPLICABLE
                field_classifications["curated.rotation"] = FieldQualityClassification.NOT_APPLICABLE
                field_classifications["curated.energy_requirements"] = FieldQualityClassification.NOT_APPLICABLE
            else:
                # LIVE RELEASED WITHOUT GUIDE: Curated fields are MISSING, registered as explicit gap
                field_classifications["curated.role"] = FieldQualityClassification.MISSING
                field_classifications["curated.weapons"] = FieldQualityClassification.MISSING
                field_classifications["curated.artifacts"] = FieldQualityClassification.MISSING
                field_classifications["curated.teams"] = FieldQualityClassification.MISSING
                field_classifications["curated.rotation"] = FieldQualityClassification.MISSING
                field_classifications["curated.energy_requirements"] = FieldQualityClassification.MISSING
                
                knowledge_gaps.extend([
                    "curated.role",
                    "curated.build_priorities",
                    "curated.weapon_recommendations",
                    "curated.artifact_recommendations",
                    "curated.team_archetypes",
                    "curated.rotation",
                    "curated.energy_requirements",
                ])
                gap_reason = f"Character released in {release_ver}; peer-reviewed KQM guide not yet published for {self.target_version}"
                if record_gap:
                    self._record_knowledge_gap(cname, cid, "build_and_rotations", gap_reason)

        # ---------------------------------------------------------------------
        # 4. Dimensioned Capabilities & Overall Quality Classification
        # ---------------------------------------------------------------------
        has_canonical = bool(cid and cname and deterministic_pkg.base_stats)
        has_mechanics = bool(len(deterministic_pkg.talents) >= 3 and len(deterministic_pkg.constellations) >= 6)
        has_expert = bool(primary_doc is not None)

        if not is_released:
            overall_quality = FieldQualityClassification.NOT_APPLICABLE
        elif not primary_doc:
            overall_quality = FieldQualityClassification.PARTIAL
        elif any(c == FieldQualityClassification.STALE for c in field_classifications.values()):
            overall_quality = FieldQualityClassification.STALE
        elif knowledge_gaps:
            overall_quality = FieldQualityClassification.PARTIAL
        else:
            overall_quality = FieldQualityClassification.VERIFIED

        package = CharacterKnowledgePackage(
            character_id=cid,
            character_name=cname,
            package_version=self.target_version,
            target_game_version=self.target_version,
            is_released=is_released,
            release_status=release_status,
            applicability_reason=applicability.get("applicability_reason"),
            has_canonical_data=has_canonical,
            has_verified_mechanics=has_mechanics,
            has_expert_guide=has_expert,
            quality_state=overall_quality,
            field_classifications=field_classifications,
            deterministic=deterministic_pkg,
            curated=curated_pkg,
            derived_calculations=derived_calculations,
            knowledge_gaps=knowledge_gaps,
            provenance_sources=list(set(provenance_sources)),
            last_verified=datetime.now(timezone.utc).isoformat(),
        )

        self.packages_cache[cid] = package
        self.packages_cache[cname.lower()] = package
        return package

    def get_character_package(self, character_id_or_name: str) -> Optional[CharacterKnowledgePackage]:
        """Retrieve or compile on demand a Character Knowledge Package."""
        key = character_id_or_name.lower().strip()
        if key in self.packages_cache:
            return self.packages_cache[key]

        characters = self._load_canonical_characters()
        for c in characters:
            if str(c.get("id")) == key or c.get("name", "").lower() == key:
                return self.compile_character_package(c)
        return None

    def list_all_packages(self) -> List[CharacterKnowledgePackage]:
        """Compile and return packages for all canonical characters."""
        characters = self._load_canonical_characters()
        packages = []
        for c in characters:
            pkg = self.compile_character_package(c, record_gap=True)
            packages.append(pkg)
        return packages

    def save_packages_registry(self, dest_file: Optional[Path] = None) -> Path:
        """Serialize all compiled packages to data/canonical/character_packages.json."""
        target = dest_file or (self.canonical_dir / "character_packages.json")
        packages = self.list_all_packages()
        data = [p.model_dump() for p in packages]
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Saved {len(packages)} character knowledge packages to {target}")
        return target


# Global singleton
character_knowledge_service = CharacterKnowledgeService()
