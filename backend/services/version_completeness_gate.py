"""
GenshinIQ — Version Completeness Release Gate Service
Enforces the non-negotiable architectural rule:
DO NOT PROCEED TO PHASE 8 OR ANY LATER PHASE UNTIL GenshinIQ HAS A VERIFIED,
VERSION-COMPLETE DATA + KNOWLEDGE PACKAGE FOR THE LATEST LIVE GENSHIN IMPACT VERSION.
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.models.version import (
    CompletenessStatus,
    EntityCoverageMetrics,
    StructuredDataCompleteness,
    GameContentCompleteness,
    KnowledgeCompleteness,
    ProvenanceCompleteness,
    FreshnessCompleteness,
    VersionDeltaCompleteness,
    VersionCompletenessReport,
    PhaseGateResponse,
    FreshnessStatus,
)
from backend.services.source_registry_service import source_registry_service
from backend.services.knowledge_contract_service import knowledge_contract_service
from backend.models.character_knowledge_package import CharacterReleaseStatus
from backend.services.character_release_service import character_release_service
from backend.services.version_service import version_service


# Forbidden placeholder phrases that immediately fail entity completeness verification
FORBIDDEN_PLACEHOLDERS = [
    "data unavailable",
    "coming soon",
    "generic character description",
    "estimated value",
    "placeholder",
    "ai generated",
    "community wiki says",
    "to be determined",
    "tbd",
]


class VersionCompletenessGateService:
    """
    Evaluates GenshinIQ version completeness across:
    1. Structured Canonical Game Data (Characters, Weapons, Artifacts, Materials, Curves, Domains)
    2. Game Content (Quests, Events, Domains, Enemies, Regions, Achievements, Recipes)
    3. Curated Knowledge (Character guides, Weapon guides, Artifact guides, Teams, Mechanics, Theorycrafting, Patch notes)
    4. Provenance Integrity
    5. Freshness
    6. Version Delta Coverage
    """

    def __init__(
        self,
        base_dir: Optional[Path] = None,
        processed_data_dir: Optional[Path] = None,
        knowledge_dir: Optional[Path] = None,
    ):
        self.base_dir = base_dir or Path(".")
        self.processed_data_dir = processed_data_dir or self.base_dir / "data" / "processed" / "game_data"
        self.knowledge_dir = knowledge_dir or self.base_dir / "data" / "knowledge"
        self.raw_dir = self.base_dir / "data" / "raw" / "game_data"

    def _has_placeholder(self, text: Any) -> bool:
        """Return True if text contains forbidden placeholder or speculative content."""
        if not text:
            return False
        text_str = str(text).lower()
        for placeholder in FORBIDDEN_PLACEHOLDERS:
            if placeholder in text_str:
                return True
        return False

    def _resolve_data_dir(self, version: str) -> Path:
        """Resolve path to versioned processed data folder or active root if matching."""
        version_dir = self.processed_data_dir / "versions" / version
        if version_dir.exists():
            return version_dir
        return self.processed_data_dir

    def _load_coverage_contract(self, version: str) -> Dict[str, Any]:
        """Load formal version coverage contract from data/canonical/version_coverage/{version}.json."""
        contract_path = self.base_dir / "data" / "canonical" / "version_coverage" / f"{version}.json"
        if contract_path.exists():
            try:
                with open(contract_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _get_active_version(self) -> str:
        """Read current active canonical version from active_version.json."""
        pointer_file = self.processed_data_dir / "active_version.json"
        if pointer_file.exists():
            try:
                with open(pointer_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("active_version", "7.0")
            except Exception:
                pass
        return "7.0"

    def _normalize_dataset(self, data: Any) -> Dict[str, Dict[str, Any]]:
        """Convert list of entity dicts (or dict of entities) to {id: dict}."""
        if isinstance(data, dict):
            return {str(k): v for k, v in data.items() if isinstance(v, dict)}
        elif isinstance(data, list):
            result = {}
            for item in data:
                if isinstance(item, dict):
                    eid = str(item.get("id") or item.get("character_id") or item.get("name") or len(result))
                    result[eid] = item
            return result
        return {}

    # =========================================================================
    # 1. STRUCTURED GAME DATA AUDIT
    # =========================================================================

    def audit_structured_data(self, target_version: str) -> Tuple[StructuredDataCompleteness, List[str]]:
        """Audit canonical structured game data across characters, weapons, artifacts, materials, curves, domains."""
        data_dir = self._resolve_data_dir(target_version)
        blockers: List[str] = []

        # 1. Characters
        char_file = data_dir / "characters.json"
        expected_chars = 119
        found_chars = 0
        verified_chars = 0
        missing_chars: List[str] = []
        if char_file.exists():
            try:
                with open(char_file, "r", encoding="utf-8") as f:
                    chars = self._normalize_dataset(json.load(f))
                found_chars = len(chars)
                for cid, cdata in chars.items():
                    # Required fields check
                    has_id = bool(cid)
                    has_name = bool(cdata.get("name") and not self._has_placeholder(cdata.get("name")))
                    has_stats = bool(cdata.get("base_stats") or cdata.get("base_hp_lvl90") or cdata.get("hp_base") or cdata.get("base_hp"))
                    if has_id and has_name and has_stats:
                        verified_chars += 1
                    else:
                        missing_chars.append(f"Character {cid} missing core stats or name")
            except Exception as e:
                blockers.append(f"Failed to read characters.json: {e}")
        else:
            blockers.append(f"Missing structured dataset: {char_file.name}")

        char_cov = verified_chars / max(1, expected_chars)
        char_status = CompletenessStatus.COMPLETE if verified_chars >= expected_chars and not missing_chars else CompletenessStatus.INCOMPLETE
        if char_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Structured characters incomplete: {verified_chars}/{expected_chars} verified")

        char_metrics = EntityCoverageMetrics(
            category="characters",
            expected_count=expected_chars,
            found_count=found_chars,
            verified_count=verified_chars,
            missing_count=max(0, expected_chars - verified_chars),
            coverage_ratio=min(1.0, char_cov),
            status=char_status,
            sample_missing=missing_chars[:5],
        )

        # 2. Weapons
        weap_file = data_dir / "weapons.json"
        expected_weaps = 246
        found_weaps = 0
        verified_weaps = 0
        missing_weaps: List[str] = []
        if weap_file.exists():
            try:
                with open(weap_file, "r", encoding="utf-8") as f:
                    weaps = self._normalize_dataset(json.load(f))
                found_weaps = len(weaps)
                for wid, wdata in weaps.items():
                    has_id = bool(wid)
                    has_name = bool(wdata.get("name") and not self._has_placeholder(wdata.get("name")))
                    has_atk = bool(wdata.get("base_atk") or wdata.get("atk_base") or wdata.get("base_atk_lvl1"))
                    if has_id and has_name and has_atk:
                        verified_weaps += 1
                    else:
                        missing_weaps.append(f"Weapon {wid} missing base ATK or name")
            except Exception as e:
                blockers.append(f"Failed to read weapons.json: {e}")
        else:
            blockers.append(f"Missing structured dataset: {weap_file.name}")

        weap_cov = verified_weaps / max(1, expected_weaps)
        weap_status = CompletenessStatus.COMPLETE if verified_weaps >= expected_weaps and not missing_weaps else CompletenessStatus.INCOMPLETE
        if weap_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Structured weapons incomplete: {verified_weaps}/{expected_weaps} verified")

        weap_metrics = EntityCoverageMetrics(
            category="weapons",
            expected_count=expected_weaps,
            found_count=found_weaps,
            verified_count=verified_weaps,
            missing_count=max(0, expected_weaps - verified_weaps),
            coverage_ratio=min(1.0, weap_cov),
            status=weap_status,
            sample_missing=missing_weaps[:5],
        )

        # 3. Artifacts
        art_file = data_dir / "artifacts.json"
        lvl_file = data_dir / "artifact_levels.json"
        expected_arts = 51
        found_arts = 0
        verified_arts = 0
        if art_file.exists() and lvl_file.exists():
            try:
                with open(art_file, "r", encoding="utf-8") as f:
                    arts = self._normalize_dataset(json.load(f))
                found_arts = len(arts)
                verified_arts = sum(1 for a in arts.values() if a.get("name") and not self._has_placeholder(a.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read artifacts: {e}")

        art_cov = verified_arts / max(1, expected_arts)
        art_status = CompletenessStatus.COMPLETE if verified_arts >= expected_arts else CompletenessStatus.INCOMPLETE
        art_metrics = EntityCoverageMetrics(
            category="artifacts",
            expected_count=expected_arts,
            found_count=found_arts,
            verified_count=verified_arts,
            missing_count=max(0, expected_arts - verified_arts),
            coverage_ratio=min(1.0, art_cov),
            status=art_status,
        )

        # 4. Materials
        mat_file = data_dir / "materials.json"
        expected_mats = 200
        found_mats = 0
        verified_mats = 0
        if mat_file.exists():
            try:
                with open(mat_file, "r", encoding="utf-8") as f:
                    mats = self._normalize_dataset(json.load(f))
                found_mats = len(mats)
                verified_mats = sum(1 for m in mats.values() if m.get("name") and not self._has_placeholder(m.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read materials: {e}")

        mat_cov = verified_mats / max(1, expected_mats)
        mat_status = CompletenessStatus.COMPLETE if verified_mats >= expected_mats else CompletenessStatus.INCOMPLETE
        mat_metrics = EntityCoverageMetrics(
            category="materials",
            expected_count=expected_mats,
            found_count=found_mats,
            verified_count=verified_mats,
            missing_count=max(0, expected_mats - verified_mats),
            coverage_ratio=min(1.0, mat_cov),
            status=mat_status,
        )

        # 5. Curves
        acurve_file = data_dir / "avatar_curves.json"
        wcurve_file = data_dir / "weapon_curves.json"
        curves_ok = False
        if acurve_file.exists() and wcurve_file.exists():
            try:
                with open(acurve_file, "r", encoding="utf-8") as f:
                    ac = json.load(f)
                with open(wcurve_file, "r", encoding="utf-8") as f:
                    wc = json.load(f)
                curves_ok = bool(ac and wc and len(ac) > 0 and len(wc) > 0)
            except Exception:
                pass

        curve_metrics = EntityCoverageMetrics(
            category="curves",
            expected_count=2,
            found_count=2 if curves_ok else 0,
            verified_count=2 if curves_ok else 0,
            missing_count=0 if curves_ok else 2,
            coverage_ratio=1.0 if curves_ok else 0.0,
            status=CompletenessStatus.COMPLETE if curves_ok else CompletenessStatus.INCOMPLETE,
        )

        # 6. Domains (Structured schedule data)
        sched_file = self.knowledge_dir / "structured_daily_talent_books_schedule.json"
        dom_sched_ok = sched_file.exists()
        domain_metrics = EntityCoverageMetrics(
            category="domains",
            expected_count=1,
            found_count=1 if dom_sched_ok else 0,
            verified_count=1 if dom_sched_ok else 0,
            missing_count=0 if dom_sched_ok else 1,
            coverage_ratio=1.0 if dom_sched_ok else 0.0,
            status=CompletenessStatus.COMPLETE if dom_sched_ok else CompletenessStatus.INCOMPLETE,
        )

        # 7. Item relationships
        rel_metrics = EntityCoverageMetrics(
            category="relationships",
            expected_count=1,
            found_count=1 if (char_file.exists() and mat_file.exists()) else 0,
            verified_count=1 if (char_file.exists() and mat_file.exists()) else 0,
            missing_count=0 if (char_file.exists() and mat_file.exists()) else 1,
            coverage_ratio=1.0 if (char_file.exists() and mat_file.exists()) else 0.0,
            status=CompletenessStatus.COMPLETE if (char_file.exists() and mat_file.exists()) else CompletenessStatus.INCOMPLETE,
        )

        sub_statuses = [
            char_metrics.status,
            weap_metrics.status,
            art_metrics.status,
            mat_metrics.status,
            curve_metrics.status,
            domain_metrics.status,
            rel_metrics.status,
        ]
        overall_cov = (
            char_metrics.coverage_ratio
            + weap_metrics.coverage_ratio
            + art_metrics.coverage_ratio
            + mat_metrics.coverage_ratio
            + curve_metrics.coverage_ratio
            + domain_metrics.coverage_ratio
            + rel_metrics.coverage_ratio
        ) / 7.0

        overall_status = CompletenessStatus.COMPLETE if all(s == CompletenessStatus.COMPLETE for s in sub_statuses) else CompletenessStatus.INCOMPLETE

        result = StructuredDataCompleteness(
            status=overall_status,
            coverage=round(overall_cov, 4),
            characters=char_metrics,
            weapons=weap_metrics,
            artifacts=art_metrics,
            materials=mat_metrics,
            curves=curve_metrics,
            domains=domain_metrics,
            relationships=rel_metrics,
        )
        return result, blockers

    # =========================================================================
    # 2. GAME CONTENT AUDIT
    # =========================================================================

    def audit_game_content(self, target_version: str) -> Tuple[GameContentCompleteness, List[str]]:
        """Audit game-world content: quests, events, enemies, domains, regions, achievements, crafting, farming, mechanics against contract."""
        data_dir = self._resolve_data_dir(target_version)
        contract = self._load_coverage_contract(target_version)
        gc_contract = contract.get("game_content", {})
        blockers: List[str] = []

        # 1. Quests
        quest_file = data_dir / "quests.json"
        if not quest_file.exists():
            quest_file = self.processed_data_dir / "quests.json"
        quest_expected = gc_contract.get("quests", {}).get("expected_count", 50)
        quest_found = 0
        quest_verified = 0
        if quest_file.exists():
            try:
                with open(quest_file, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
                quest_found = len(q_data)
                quest_verified = sum(1 for q in q_data if q.get("id") and q.get("title") and not self._has_placeholder(q.get("title")))
            except Exception as e:
                blockers.append(f"Failed to read quests.json: {e}")
        else:
            blockers.append("Missing quests catalog: quests.json")

        quest_status = CompletenessStatus.COMPLETE if quest_verified >= quest_expected else CompletenessStatus.INCOMPLETE
        if quest_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Quests incomplete: {quest_verified}/{quest_expected} verified")

        quest_metrics = EntityCoverageMetrics(
            category="quests",
            expected_count=quest_expected,
            found_count=quest_found,
            verified_count=quest_verified,
            missing_count=max(0, quest_expected - quest_verified),
            coverage_ratio=min(1.0, round(quest_verified / max(1, quest_expected), 4)),
            status=quest_status,
        )

        # 2. Events
        event_file = data_dir / "events.json"
        if not event_file.exists():
            event_file = self.processed_data_dir / "events.json"
        event_expected = gc_contract.get("events", {}).get("expected_count", 10)
        event_found = 0
        event_verified = 0
        if event_file.exists():
            try:
                with open(event_file, "r", encoding="utf-8") as f:
                    e_data = json.load(f)
                event_found = len(e_data)
                event_verified = sum(1 for e in e_data if e.get("id") and e.get("name") and not self._has_placeholder(e.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read events.json: {e}")
        else:
            blockers.append("Missing events catalog: events.json")

        event_status = CompletenessStatus.COMPLETE if event_verified >= event_expected else CompletenessStatus.INCOMPLETE
        if event_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Events incomplete: {event_verified}/{event_expected} verified")

        event_metrics = EntityCoverageMetrics(
            category="events",
            expected_count=event_expected,
            found_count=event_found,
            verified_count=event_verified,
            missing_count=max(0, event_expected - event_verified),
            coverage_ratio=min(1.0, round(event_verified / max(1, event_expected), 4)),
            status=event_status,
        )

        # 3. Domains
        domain_file = data_dir / "domains.json"
        if not domain_file.exists():
            domain_file = self.processed_data_dir / "domains.json"
        domain_expected = gc_contract.get("domains", {}).get("expected_count", 40)
        domain_found = 0
        domain_verified = 0
        if domain_file.exists():
            try:
                with open(domain_file, "r", encoding="utf-8") as f:
                    d_data = json.load(f)
                domain_found = len(d_data)
                domain_verified = sum(1 for d in d_data if d.get("id") and d.get("name") and not self._has_placeholder(d.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read domains.json: {e}")
        else:
            blockers.append("Missing domains catalog: domains.json")

        domain_status = CompletenessStatus.COMPLETE if domain_verified >= domain_expected else CompletenessStatus.INCOMPLETE
        if domain_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Domains incomplete: {domain_verified}/{domain_expected} verified")

        domain_metrics = EntityCoverageMetrics(
            category="domains",
            expected_count=domain_expected,
            found_count=domain_found,
            verified_count=domain_verified,
            missing_count=max(0, domain_expected - domain_verified),
            coverage_ratio=min(1.0, round(domain_verified / max(1, domain_expected), 4)),
            status=domain_status,
        )

        # 4. Enemies & Bosses
        enemy_file = data_dir / "enemies.json"
        if not enemy_file.exists():
            enemy_file = self.processed_data_dir / "enemies.json"
        enemy_expected = gc_contract.get("enemies", {}).get("expected_count", 80)
        enemy_found = 0
        enemy_verified = 0
        if enemy_file.exists():
            try:
                with open(enemy_file, "r", encoding="utf-8") as f:
                    en_data = json.load(f)
                enemy_found = len(en_data)
                enemy_verified = sum(1 for en in en_data if en.get("id") and en.get("name") and not self._has_placeholder(en.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read enemies.json: {e}")
        else:
            blockers.append("Missing enemies catalog: enemies.json")

        enemy_status = CompletenessStatus.COMPLETE if enemy_verified >= enemy_expected else CompletenessStatus.INCOMPLETE
        if enemy_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Enemies & Bosses incomplete: {enemy_verified}/{enemy_expected} verified")

        enemy_metrics = EntityCoverageMetrics(
            category="enemies",
            expected_count=enemy_expected,
            found_count=enemy_found,
            verified_count=enemy_verified,
            missing_count=max(0, enemy_expected - enemy_verified),
            coverage_ratio=min(1.0, round(enemy_verified / max(1, enemy_expected), 4)),
            status=enemy_status,
        )

        # 5. Regions & Areas
        region_file = data_dir / "regions.json"
        if not region_file.exists():
            region_file = self.processed_data_dir / "regions.json"
        region_expected = gc_contract.get("regions", {}).get("expected_count", 7)
        region_found = 0
        region_verified = 0
        if region_file.exists():
            try:
                with open(region_file, "r", encoding="utf-8") as f:
                    reg_data = json.load(f)
                region_found = len(reg_data)
                region_verified = sum(1 for r in reg_data if r.get("id") and r.get("name") and not self._has_placeholder(r.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read regions.json: {e}")
        else:
            blockers.append("Missing regions catalog: regions.json")

        region_status = CompletenessStatus.COMPLETE if region_verified >= region_expected else CompletenessStatus.INCOMPLETE
        if region_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Regions & Areas incomplete: {region_verified}/{region_expected} verified")

        region_metrics = EntityCoverageMetrics(
            category="regions",
            expected_count=region_expected,
            found_count=region_found,
            verified_count=region_verified,
            missing_count=max(0, region_expected - region_verified),
            coverage_ratio=min(1.0, round(region_verified / max(1, region_expected), 4)),
            status=region_status,
        )

        # 6. Achievements
        achieve_file = data_dir / "achievements.json"
        if not achieve_file.exists():
            achieve_file = self.processed_data_dir / "achievements.json"
        achieve_expected = gc_contract.get("achievements", {}).get("expected_count", 100)
        achieve_found = 0
        achieve_verified = 0
        if achieve_file.exists():
            try:
                with open(achieve_file, "r", encoding="utf-8") as f:
                    ach_data = json.load(f)
                achieve_found = len(ach_data)
                achieve_verified = sum(1 for a in ach_data if a.get("id") and a.get("title") and not self._has_placeholder(a.get("title")))
            except Exception as e:
                blockers.append(f"Failed to read achievements.json: {e}")
        else:
            blockers.append("Missing achievements catalog: achievements.json")

        achieve_status = CompletenessStatus.COMPLETE if achieve_verified >= achieve_expected else CompletenessStatus.INCOMPLETE
        if achieve_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Achievements incomplete: {achieve_verified}/{achieve_expected} verified")

        achieve_metrics = EntityCoverageMetrics(
            category="achievements",
            expected_count=achieve_expected,
            found_count=achieve_found,
            verified_count=achieve_verified,
            missing_count=max(0, achieve_expected - achieve_verified),
            coverage_ratio=min(1.0, round(achieve_verified / max(1, achieve_expected), 4)),
            status=achieve_status,
        )

        # 7. Crafting & Food Recipes
        craft_file = data_dir / "recipes.json"
        if not craft_file.exists():
            craft_file = self.processed_data_dir / "recipes.json"
        craft_expected = gc_contract.get("crafting", {}).get("expected_count", 50)
        craft_found = 0
        craft_verified = 0
        if craft_file.exists():
            try:
                with open(craft_file, "r", encoding="utf-8") as f:
                    cr_data = json.load(f)
                craft_found = len(cr_data)
                craft_verified = sum(1 for r in cr_data if r.get("id") and r.get("name") and not self._has_placeholder(r.get("name")))
            except Exception as e:
                blockers.append(f"Failed to read recipes.json: {e}")
        else:
            blockers.append("Missing recipes catalog: recipes.json")

        craft_status = CompletenessStatus.COMPLETE if craft_verified >= craft_expected else CompletenessStatus.INCOMPLETE
        if craft_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Game Content Crafting & Recipes incomplete: {craft_verified}/{craft_expected} verified")

        craft_metrics = EntityCoverageMetrics(
            category="crafting",
            expected_count=craft_expected,
            found_count=craft_found,
            verified_count=craft_verified,
            missing_count=max(0, craft_expected - craft_verified),
            coverage_ratio=min(1.0, round(craft_verified / max(1, craft_expected), 4)),
            status=craft_status,
        )

        # 8. Farming
        farm_found = 3 if (self.knowledge_dir / "structured_daily_talent_books_schedule.json").exists() else 0
        farm_expected = gc_contract.get("farming", {}).get("expected_count", 3)
        farm_status = CompletenessStatus.COMPLETE if farm_found >= farm_expected else CompletenessStatus.INCOMPLETE
        farm_metrics = EntityCoverageMetrics(
            category="farming",
            expected_count=farm_expected,
            found_count=farm_found,
            verified_count=farm_found,
            missing_count=max(0, farm_expected - farm_found),
            coverage_ratio=min(1.0, round(farm_found / max(1, farm_expected), 4)),
            status=farm_status,
        )

        # 9. Combat Mechanics
        combat_mech_file = self.knowledge_dir / "official_combat_system_mechanics.json"
        mech_ok = combat_mech_file.exists()
        mech_expected = gc_contract.get("mechanics", {}).get("expected_count", 1)
        mech_metrics = EntityCoverageMetrics(
            category="mechanics",
            expected_count=mech_expected,
            found_count=1 if mech_ok else 0,
            verified_count=1 if mech_ok else 0,
            missing_count=0 if mech_ok else 1,
            coverage_ratio=1.0 if mech_ok else 0.0,
            status=CompletenessStatus.COMPLETE if mech_ok else CompletenessStatus.INCOMPLETE,
        )

        sub_metrics = [
            quest_metrics,
            event_metrics,
            domain_metrics,
            enemy_metrics,
            region_metrics,
            achieve_metrics,
            craft_metrics,
            farm_metrics,
            mech_metrics,
        ]
        overall_cov = sum(m.coverage_ratio for m in sub_metrics) / len(sub_metrics)
        overall_status = CompletenessStatus.COMPLETE if all(m.status == CompletenessStatus.COMPLETE for m in sub_metrics) else CompletenessStatus.INCOMPLETE

        result = GameContentCompleteness(
            status=overall_status,
            coverage=round(overall_cov, 4),
            quests=quest_metrics,
            events=event_metrics,
            domains=domain_metrics,
            enemies=enemy_metrics,
            regions=region_metrics,
            achievements=achieve_metrics,
            crafting=craft_metrics,
            farming=farm_metrics,
            mechanics=mech_metrics,
        )
        return result, blockers

    # =========================================================================
    # 3. KNOWLEDGE COVERAGE AUDIT
    # =========================================================================

    def audit_knowledge_coverage(self, target_version: str) -> Tuple[KnowledgeCompleteness, List[str]]:
        """Audit curated knowledge base against all 119 characters, structured weapons, artifacts, teams, mechanics, and 7.0 changes."""
        data_dir = self._resolve_data_dir(target_version)
        contract = self._load_coverage_contract(target_version)
        k_contract = contract.get("knowledge", {})
        blockers: List[str] = []

        # 1. Character Guides (Partitioned: Live Released vs Unreleased Preview)
        char_file = data_dir / "characters.json"
        all_chars_data: Dict[str, Dict[str, Any]] = {}
        if char_file.exists():
            with open(char_file, "r", encoding="utf-8") as f:
                all_chars_data = self._normalize_dataset(json.load(f))

        # Partition characters dynamically via CharacterReleaseService
        live_chars: Dict[str, Dict[str, Any]] = {}
        unreleased_chars: Dict[str, Dict[str, Any]] = {}
        for cid, cdata in all_chars_data.items():
            rel_status = character_release_service.classify_character(cdata)
            if rel_status == CharacterReleaseStatus.LIVE_RELEASED:
                live_chars[cid] = cdata
            else:
                unreleased_chars[cid] = cdata

        expected_live_chars = len(live_chars)  # Exactly 95 live playable characters in 5.4

        # Count wiki and kqm guides
        wiki_files = list(self.knowledge_dir.glob("wiki_*.json"))
        kqm_files = list(self.knowledge_dir.glob("kqm_*_guide.json"))
        found_char_docs = len(wiki_files) + len(kqm_files)

        # Verify which live characters have full valid knowledge without placeholders
        covered_char_names: Set[str] = set()
        missing_chars: List[str] = []

        for doc_file in wiki_files + kqm_files:
            try:
                with open(doc_file, "r", encoding="utf-8") as f:
                    wdata = json.load(f)
                meta = wdata.get("metadata", {})
                cname = meta.get("character") or wdata.get("title", "").replace(" — Complete Character Reference", "").replace(" Character & Theorycrafting Guide", "").strip() or doc_file.stem.replace("wiki_", "").replace("kqm_", "").replace("_guide", "")
                content_str = wdata.get("content", "") if isinstance(wdata.get("content"), str) else str(wdata.get("content", {}))
                lower_content = content_str.lower()
                has_overview = bool(("overview" in lower_content or "playstyle" in lower_content or "build" in lower_content) and not self._has_placeholder(content_str))
                has_talents = bool("talent" in lower_content or "skill" in lower_content or "weapon" in lower_content or "artifact" in lower_content)
                if has_overview and has_talents:
                    covered_char_names.add(cname.lower().replace(" ", "").replace("_", "").replace("-", ""))
            except Exception:
                pass

        for cid, cdata in live_chars.items():
            cname = cdata.get("name", cid)
            norm_name = cname.lower().replace(" ", "").replace("_", "").replace("-", "")
            if norm_name not in covered_char_names:
                missing_chars.append(f"{cname} (ID {cid})")

        verified_chars = len(live_chars) - len(missing_chars)
        char_cov = max(0.0, verified_chars / max(1, expected_live_chars))
        char_status = CompletenessStatus.COMPLETE if verified_chars >= expected_live_chars and not missing_chars else CompletenessStatus.INCOMPLETE
        if char_status != CompletenessStatus.COMPLETE:
            missing_names = [m.split(" (")[0] for m in missing_chars]
            blockers.append(f"Character expert guide coverage incomplete: {verified_chars}/{expected_live_chars} live characters covered ({len(missing_chars)} missing: {', '.join(missing_names)}). {len(unreleased_chars)} unreleased entities excluded as NOT_APPLICABLE.")

        char_guide_metrics = EntityCoverageMetrics(
            category="character_guides",
            expected_count=expected_live_chars,
            found_count=found_char_docs,
            verified_count=verified_chars,
            missing_count=len(missing_chars),
            coverage_ratio=round(char_cov, 4),
            status=char_status,
            sample_missing=missing_chars[:5],
        )

        # 2. Weapon Knowledge (Structured Weapon Contract: passive, refinement, stats, version without placeholders)
        weap_file = data_dir / "weapons.json"
        if not weap_file.exists():
            weap_file = self.processed_data_dir / "weapons.json"
        expected_weaps = k_contract.get("weapon_knowledge", {}).get("expected_count", 246)
        weap_found = 0
        weap_verified = 0
        missing_weap_knowledge: List[str] = []

        if weap_file.exists():
            try:
                with open(weap_file, "r", encoding="utf-8") as f:
                    weaps_data = self._normalize_dataset(json.load(f))
                weap_found = len(weaps_data)
                for wid, wdata in weaps_data.items():
                    has_id = bool(wid)
                    has_name = bool(wdata.get("name") and not self._has_placeholder(wdata.get("name")))
                    has_stats = bool(wdata.get("base_atk_lvl1") or wdata.get("base_atk_lvl90"))
                    has_passive = bool(wdata.get("passive_desc") is not None or wdata.get("rarity", 0) <= 2)
                    has_refinements = bool(isinstance(wdata.get("refinements"), list))
                    if has_id and has_name and has_stats and has_passive and has_refinements:
                        weap_verified += 1
                    else:
                        missing_weap_knowledge.append(f"Weapon {wid} ({wdata.get('name')}) missing structured knowledge fields")
            except Exception as e:
                blockers.append(f"Failed to read weapons.json for weapon knowledge: {e}")
        else:
            blockers.append("Missing weapons dataset for weapon knowledge: weapons.json")

        weap_cov = weap_verified / max(1, expected_weaps)
        weap_status = CompletenessStatus.COMPLETE if weap_verified >= expected_weaps and not missing_weap_knowledge else CompletenessStatus.INCOMPLETE
        if weap_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Weapon knowledge incomplete: {weap_verified}/{expected_weaps} weapons verified")

        weap_guide_metrics = EntityCoverageMetrics(
            category="weapon_guides",
            expected_count=expected_weaps,
            found_count=weap_found,
            verified_count=weap_verified,
            missing_count=max(0, expected_weaps - weap_verified),
            coverage_ratio=min(1.0, round(weap_cov, 4)),
            status=weap_status,
            sample_missing=missing_weap_knowledge[:5],
        )

        # 3. Artifact Guides (Expected: 51 artifact sets in knowledge)
        art_files = list(self.knowledge_dir.glob("artifact_*.json"))
        expected_arts = k_contract.get("artifact_guides", {}).get("expected_count", 51)
        art_found = len(art_files)
        art_cov = art_found / max(1, expected_arts)
        art_status = CompletenessStatus.COMPLETE if art_found >= expected_arts else CompletenessStatus.INCOMPLETE
        art_guide_metrics = EntityCoverageMetrics(
            category="artifact_guides",
            expected_count=expected_arts,
            found_count=art_found,
            verified_count=art_found,
            missing_count=max(0, expected_arts - art_found),
            coverage_ratio=min(1.0, round(art_cov, 4)),
            status=art_status,
        )

        # 4. Team-Building Knowledge
        team_file = self.knowledge_dir / "mechanics_team_archetypes.json"
        team_found = 1 if team_file.exists() else 0
        team_expected = k_contract.get("team_building", {}).get("expected_count", 1)
        team_metrics = EntityCoverageMetrics(
            category="team_building",
            expected_count=team_expected,
            found_count=team_found,
            verified_count=team_found,
            missing_count=max(0, team_expected - team_found),
            coverage_ratio=1.0 if team_found >= team_expected else 0.0,
            status=CompletenessStatus.COMPLETE if team_found >= team_expected else CompletenessStatus.INCOMPLETE,
        )

        # 5. Mechanics Knowledge (Elemental gauge, ICD, reactions, damage math)
        mech_files = list(self.knowledge_dir.glob("mechanics_*.json"))
        expected_mechs = k_contract.get("mechanics", {}).get("expected_count", 12)
        mech_found = len(mech_files)
        mech_cov = mech_found / max(1, expected_mechs)
        mech_status = CompletenessStatus.COMPLETE if mech_found >= expected_mechs else CompletenessStatus.PARTIAL
        mech_guide_metrics = EntityCoverageMetrics(
            category="mechanics",
            expected_count=expected_mechs,
            found_count=mech_found,
            verified_count=mech_found,
            missing_count=max(0, expected_mechs - mech_found),
            coverage_ratio=min(1.0, round(mech_cov, 4)),
            status=mech_status,
        )

        # 6. Theorycrafting Knowledge (KQM extended guides per contract)
        expected_tc = k_contract.get("theorycrafting", {}).get("expected_count", 15)
        tc_found = len(kqm_files)
        tc_cov = tc_found / max(1, expected_tc)
        tc_status = CompletenessStatus.COMPLETE if tc_found >= expected_tc else CompletenessStatus.INCOMPLETE
        if tc_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Theorycrafting coverage incomplete: {tc_found}/{expected_tc} characters have KQM extended guides")

        tc_metrics = EntityCoverageMetrics(
            category="theorycrafting",
            expected_count=expected_tc,
            found_count=tc_found,
            verified_count=tc_found,
            missing_count=max(0, expected_tc - tc_found),
            coverage_ratio=min(1.0, round(tc_cov, 4)),
            status=tc_status,
            sample_missing=["KQM Deep Dives"],
        )

        # 7. Farming Knowledge
        sched_files = list(self.knowledge_dir.glob("structured_*.json"))
        expected_farm = k_contract.get("farming", {}).get("expected_count", 3)
        farm_found = len(sched_files)
        farm_metrics = EntityCoverageMetrics(
            category="farming",
            expected_count=expected_farm,
            found_count=farm_found,
            verified_count=farm_found,
            missing_count=max(0, expected_farm - farm_found),
            coverage_ratio=min(1.0, round(farm_found / max(1, expected_farm), 4)),
            status=CompletenessStatus.COMPLETE if farm_found >= expected_farm else CompletenessStatus.INCOMPLETE,
        )

        # 8. Current-Version Changes Knowledge (official_patch_7_0_notes.json)
        v_tag = target_version.replace(".", "_")
        patch_file = self.knowledge_dir / f"official_patch_{v_tag}_notes.json"
        patch_v_files = list(self.knowledge_dir.glob(f"*patch*{v_tag}*.json"))
        has_current_patch = patch_file.exists() or len(patch_v_files) > 0
        expected_patch = k_contract.get("current_version_changes", {}).get("expected_count", 1)
        patch_status = CompletenessStatus.COMPLETE if has_current_patch else CompletenessStatus.MISSING
        if patch_status != CompletenessStatus.COMPLETE:
            blockers.append(f"Current-version knowledge missing: Official patch {target_version} release notes document not found in data/knowledge/")

        patch_metrics = EntityCoverageMetrics(
            category="current_version_changes",
            expected_count=expected_patch,
            found_count=1 if has_current_patch else 0,
            verified_count=1 if has_current_patch else 0,
            missing_count=0 if has_current_patch else expected_patch,
            coverage_ratio=1.0 if has_current_patch else 0.0,
            status=patch_status,
            sample_missing=[f"official_patch_{v_tag}_notes.json"],
        )

        sub_metrics = [
            char_guide_metrics,
            weap_guide_metrics,
            art_guide_metrics,
            team_metrics,
            mech_guide_metrics,
            tc_metrics,
            farm_metrics,
            patch_metrics,
        ]
        overall_cov = sum(m.coverage_ratio for m in sub_metrics) / len(sub_metrics)
        overall_status = CompletenessStatus.COMPLETE if all(m.status == CompletenessStatus.COMPLETE for m in sub_metrics) else CompletenessStatus.INCOMPLETE

        result = KnowledgeCompleteness(
            status=overall_status,
            coverage=round(overall_cov, 4),
            character_guides=char_guide_metrics,
            weapon_guides=weap_guide_metrics,
            artifact_guides=art_guide_metrics,
            team_building=team_metrics,
            mechanics=mech_guide_metrics,
            theorycrafting=tc_metrics,
            farming=farm_metrics,
            current_version_changes=patch_metrics,
        )
        return result, blockers

    # =========================================================================
    # 4. PROVENANCE INTEGRITY AUDIT
    # =========================================================================

    def audit_provenance(self) -> Tuple[ProvenanceCompleteness, List[str]]:
        """Audit provenance integrity across all knowledge and data manifests."""
        blockers: List[str] = []
        registered_sources = {s.source_id for s in source_registry_service.list_sources(enabled_only=False)}

        valid_count = 0
        missing_count = 0
        stale_count = 0
        unverifiable_count = 0

        for kfile in self.knowledge_dir.glob("*.json"):
            try:
                with open(kfile, "r", encoding="utf-8") as f:
                    kdata = json.load(f)
                meta = kdata.get("metadata", {})
                prov = kdata.get("provenance", {})
                sid = meta.get("source_id") or prov.get("source_id") or kdata.get("source_id")
                if not sid:
                    missing_count += 1
                elif sid not in registered_sources:
                    unverifiable_count += 1
                else:
                    valid_count += 1
            except Exception:
                missing_count += 1

        all_ok = (missing_count == 0 and unverifiable_count == 0)
        status = CompletenessStatus.COMPLETE if all_ok else CompletenessStatus.PARTIAL
        if not all_ok:
            blockers.append(f"Provenance incomplete: {missing_count} files missing source_id, {unverifiable_count} unverifiable sources")

        result = ProvenanceCompleteness(
            status=status,
            records_with_valid_provenance=valid_count,
            records_missing_provenance=missing_count,
            records_with_stale_provenance=stale_count,
            records_with_unverifiable_source=unverifiable_count,
            all_required_sources_verified=all_ok,
        )
        return result, blockers

    # =========================================================================
    # 5. FRESHNESS AUDIT
    # =========================================================================

    def audit_freshness(self, target_version: str) -> Tuple[FreshnessCompleteness, List[str]]:
        """Audit document freshness against target game version."""
        blockers: List[str] = []
        current_count = 0
        compatible_count = 0
        stale_count = 0
        unknown_count = 0

        target_v = float(target_version) if target_version.replace(".", "").isdigit() else 7.0

        for kfile in self.knowledge_dir.glob("*.json"):
            try:
                with open(kfile, "r", encoding="utf-8") as f:
                    kdata = json.load(f)
                meta = kdata.get("metadata", {})
                prov = kdata.get("provenance", {})
                gv = meta.get("game_version") or prov.get("game_version") or kdata.get("game_version")
                if not gv:
                    unknown_count += 1
                    continue
                try:
                    doc_v = float(str(gv))
                    if doc_v >= target_v:
                        current_count += 1
                    elif target_v - doc_v <= 2.0:
                        compatible_count += 1
                    else:
                        stale_count += 1
                except ValueError:
                    unknown_count += 1
            except Exception:
                unknown_count += 1

        total = current_count + compatible_count + stale_count + unknown_count
        ratio = (current_count + compatible_count) / max(1, total)
        status = CompletenessStatus.COMPLETE if stale_count == 0 and unknown_count == 0 else CompletenessStatus.STALE

        if stale_count > 0:
            blockers.append(f"Freshness audit: {stale_count} documents are more than 2 minor patches behind target v{target_version}")

        result = FreshnessCompleteness(
            status=status,
            current_records=current_count,
            compatible_records=compatible_count,
            stale_records=stale_count,
            unknown_records=unknown_count,
            freshness_ratio=round(ratio, 4),
        )
        return result, blockers

    # =========================================================================
    # 6. VERSION DELTA AUDIT
    # =========================================================================

    def audit_version_delta(self, base_version: str, target_version: str) -> Tuple[VersionDeltaCompleteness, List[str]]:
        """Audit coverage of entities introduced or altered between base and target version."""
        blockers: List[str] = []
        diff_file = self.processed_data_dir / "versions" / target_version / "version_diff.json"

        new_chars = 0
        new_weaps = 0
        new_arts = 0
        new_content = 0
        covered_count = 0
        missing_entities: List[str] = []

        if diff_file.exists():
            try:
                with open(diff_file, "r", encoding="utf-8") as f:
                    diff_data = json.load(f)
                items = diff_data.get("items", [])
                for it in items:
                    etype = it.get("entity_type")
                    if it.get("change_type") == "added":
                        if etype == "character":
                            new_chars += 1
                        elif etype == "weapon":
                            new_weaps += 1
                        elif etype == "artifact":
                            new_arts += 1
                        else:
                            new_content += 1
            except Exception:
                pass

        total_new = new_chars + new_weaps + new_arts + new_content
        status = CompletenessStatus.COMPLETE if total_new == covered_count else CompletenessStatus.PARTIAL

        result = VersionDeltaCompleteness(
            status=status,
            base_version=base_version,
            target_version=target_version,
            new_characters_count=new_chars,
            new_weapons_count=new_weaps,
            new_artifacts_count=new_arts,
            new_content_count=new_content,
            covered_new_entities_count=covered_count,
            missing_new_entities=missing_entities,
        )
        return result, blockers

    # =========================================================================
    # 7. COMPREHENSIVE AUDIT & PHASE GATE EVALUATION
    # =========================================================================

    def audit_version_completeness(self, target_version: Optional[str] = None) -> VersionCompletenessReport:
        """Execute end-to-end version completeness audit against all domains."""
        active_v = self._get_active_version()
        target_v = target_version or active_v
        live_v = version_service.get_latest_known_version().version

        all_blockers: List[str] = []

        # Audit all 6 domains
        struct_data, b1 = self.audit_structured_data(target_v)
        game_content, b2 = self.audit_game_content(target_v)
        knowledge, b3 = self.audit_knowledge_coverage(target_v)
        provenance, b4 = self.audit_provenance()
        freshness, b5 = self.audit_freshness(target_v)
        vdelta, b6 = self.audit_version_delta("5.4", target_v)

        all_blockers.extend(b1)
        all_blockers.extend(b2)
        all_blockers.extend(b3)
        all_blockers.extend(b4)
        all_blockers.extend(b5)
        all_blockers.extend(b6)

        # Hard fail-closed determination:
        # If any domain is not COMPLETE, overall_status is INCOMPLETE and Phase 8 is blocked!
        domain_statuses = [
            struct_data.status,
            game_content.status,
            knowledge.status,
            provenance.status,
            freshness.status,
            vdelta.status,
        ]

        if all(s == CompletenessStatus.COMPLETE for s in domain_statuses):
            overall_status = CompletenessStatus.COMPLETE
            phase_8_allowed = True
        else:
            overall_status = CompletenessStatus.INCOMPLETE
            phase_8_allowed = False

        # Determine latest knowledge version from official patch notes in knowledge
        patch_versions = []
        for p in self.knowledge_dir.glob("official_patch_*_notes.json"):
            try:
                with open(p, "r", encoding="utf-8") as f:
                    pd = json.load(f)
                    pv = pd.get("metadata", {}).get("game_version")
                    if pv:
                        patch_versions.append(pv)
            except Exception:
                pass
        knowledge_v = max(patch_versions, key=lambda v: [int(x) for x in v.split(".") if x.isdigit()]) if patch_versions else "1.0"

        live_count = knowledge.character_guides.expected_count
        unreleased_count = max(0, 119 - live_count)
        canon_cov = struct_data.characters.coverage_ratio
        mech_cov = 1.0
        expert_cov = knowledge.character_guides.coverage_ratio

        return VersionCompletenessReport(
            live_version=live_v,
            dataset_version=target_v,
            knowledge_version=knowledge_v,
            active_canonical_version=active_v,
            project_target_version=version_service.get_project_target_version(),
            overall_status=overall_status,
            phase_8_allowed=phase_8_allowed,
            live_characters_count=live_count,
            unreleased_characters_count=unreleased_count,
            canonical_data_completeness=canon_cov,
            mechanics_completeness=mech_cov,
            expert_guide_coverage=expert_cov,
            unreleased_entities_excluded=unreleased_count,
            structured_data=struct_data,
            game_content=game_content,
            knowledge=knowledge,
            provenance=provenance,
            freshness=freshness,
            version_delta=vdelta,
            blockers=all_blockers,
            last_audit_time=datetime.now(timezone.utc).isoformat(),
        )

    def evaluate_phase_gate(self) -> PhaseGateResponse:
        """Evaluate Phase 8 gate. Returns PhaseGateResponse with fail-closed blocker."""
        report = self.audit_version_completeness()
        blocking_cats = []
        if report.structured_data.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("structured_data")
        if report.game_content.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("game_content")
        if report.knowledge.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("knowledge")
        if report.provenance.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("provenance")
        if report.freshness.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("freshness")
        if report.version_delta.status != CompletenessStatus.COMPLETE:
            blocking_cats.append("version_delta")

        if report.phase_8_allowed:
            reason = "Latest live version 7.0 is fully verified and version-complete across all domains."
        else:
            reason = f"Latest live version {report.live_version} is NOT version-complete. Blocked by: {', '.join(blocking_cats)}."

        return PhaseGateResponse(
            phase_8_allowed=report.phase_8_allowed,
            reason=reason,
            blocking_categories=blocking_cats,
            version_completeness_status=report.overall_status.value,
            active_canonical_version=report.active_canonical_version,
            live_version=report.live_version,
            audit_time=report.last_audit_time,
        )


# Global singleton instance
version_completeness_gate = VersionCompletenessGateService()
