"""
GenshinIQ — Knowledge Contract Service
Enforces the finite, evidence-based GenshinIQ Knowledge Contract (data/canonical/knowledge_contract.json).
Evaluates domain requirements, required fields, quality states, and source derivation independence.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.models.knowledge import KnowledgeQualityState, EvidenceClassification
from backend.models.source_registry import SourceTier
from backend.services.source_registry_service import source_registry_service


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


class KnowledgeContractService:
    """Service to load, evaluate, and audit against data/canonical/knowledge_contract.json."""

    def __init__(self, contract_path: Optional[Path] = None):
        self.contract_path = contract_path or Path("data/canonical/knowledge_contract.json")
        self._contract_data: Optional[Dict[str, Any]] = None

    def load_contract(self) -> Dict[str, Any]:
        """Load and cache the formal knowledge contract."""
        if self._contract_data is None:
            if not self.contract_path.exists():
                raise FileNotFoundError(f"Knowledge contract not found at {self.contract_path}")
            with open(self.contract_path, "r", encoding="utf-8") as f:
                self._contract_data = json.load(f)
        return self._contract_data

    def reload(self) -> Dict[str, Any]:
        """Force reload of the contract."""
        self._contract_data = None
        return self.load_contract()

    def get_contract(self) -> Dict[str, Any]:
        return self.load_contract()

    def get_domain_contract(self, domain_key: str) -> Dict[str, Any]:
        """Retrieve contract rules for a specific knowledge domain."""
        contract = self.load_contract()
        domains = contract.get("domains", {})
        if domain_key not in domains:
            raise KeyError(f"Domain '{domain_key}' not defined in knowledge contract")
        return domains[domain_key]

    def has_forbidden_placeholder(self, value: Any) -> bool:
        """Return True if value contains any forbidden speculative or placeholder text."""
        if value is None:
            return False
        val_str = str(value).lower()
        for placeholder in FORBIDDEN_PLACEHOLDERS:
            if placeholder in val_str:
                return True
        return False

    def validate_source_independence(self, source_id_a: str, source_id_b: str) -> bool:
        """
        Validates whether two sources are independent.
        Returns False if one source derives directly or transitively from the other.
        """
        if source_id_a == source_id_b:
            return False

        src_a = source_registry_service.get_source(source_id_a)
        src_b = source_registry_service.get_source(source_id_b)

        all_sources = {s.source_id: s for s in source_registry_service.list_sources(enabled_only=False)}

        if src_a and src_a.is_derived_from(source_id_b, all_sources):
            return False
        if src_b and src_b.is_derived_from(source_id_a, all_sources):
            return False

        return True

    def validate_character_package(
        self,
        character_id: str,
        character_name: str,
        structured_data: Optional[Dict[str, Any]],
        knowledge_doc: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Validates character knowledge package against contractual requirements:
        - Deterministic fields (identity, element, weapon_type, rarity, stats, talents, constellations)
        - Curated fields (role, build_priorities, weapon_recommendations, artifact_recommendations, rotation, ER)
        Returns quality state and missing required fields.
        """
        domain = self.get_domain_contract("character_knowledge")
        req_deterministic = domain["required_fields"]["deterministic"]
        req_curated = domain["required_fields"]["curated"]

        missing_fields: List[str] = []

        # 1. Audit deterministic fields
        if not structured_data:
            missing_fields.extend([f"deterministic.{f}" for f in req_deterministic])
        else:
            if not structured_data.get("id"):
                missing_fields.append("deterministic.identity")
            if not structured_data.get("element"):
                missing_fields.append("deterministic.element")
            if not structured_data.get("weapon_type"):
                missing_fields.append("deterministic.weapon_type")
            if not structured_data.get("rarity"):
                missing_fields.append("deterministic.rarity")
            base_stats = structured_data.get("base_stats") or {}
            hp = structured_data.get("base_hp_lvl90") or base_stats.get("hp") or structured_data.get("hp_base")
            if not hp or hp <= 0:
                missing_fields.append("deterministic.base_stats")
            talents = structured_data.get("talents") or []
            if len(talents) < 3:
                missing_fields.append("deterministic.talents")
            constellations = structured_data.get("constellations") or []
            if len(constellations) < 6:
                missing_fields.append("deterministic.constellations")

        # 2. Audit curated fields
        if not knowledge_doc:
            missing_fields.extend([f"curated.{f}" for f in req_curated])
        else:
            content_str = knowledge_doc.get("content", "")
            if isinstance(content_str, dict):
                content_str = json.dumps(content_str)

            if self.has_forbidden_placeholder(content_str):
                missing_fields.append("curated.forbidden_placeholder_detected")

            # Check core curated sections
            lower_content = content_str.lower()
            if "role" not in lower_content and "overview" not in lower_content:
                missing_fields.append("curated.role")
            if "weapon" not in lower_content and "weapons" not in lower_content:
                missing_fields.append("curated.weapon_recommendations")
            if "artifact" not in lower_content and "artifacts" not in lower_content:
                missing_fields.append("curated.artifact_recommendations")
            if "team" not in lower_content and "synergy" not in lower_content:
                missing_fields.append("curated.team_archetypes")

        # Determine quality state
        if not structured_data and not knowledge_doc:
            quality_state = KnowledgeQualityState.UNKNOWN
        elif missing_fields:
            quality_state = KnowledgeQualityState.PARTIAL
        else:
            quality_state = KnowledgeQualityState.VERIFIED

        return {
            "character_id": character_id,
            "character_name": character_name,
            "quality_state": quality_state.value,
            "is_complete": len(missing_fields) == 0,
            "missing_fields": missing_fields,
            "deterministic_available": structured_data is not None,
            "curated_available": knowledge_doc is not None,
        }

    def validate_weapon_package(self, weapon_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates weapon knowledge package per contract:
        Structured weapon data (base ATK, secondary stat, passive, refinements) satisfies weapon capability.
        """
        domain = self.get_domain_contract("weapon_knowledge")
        missing_fields = []

        wid = weapon_data.get("id")
        name = weapon_data.get("name")
        wtype = weapon_data.get("weapon_type")
        rarity = weapon_data.get("rarity", 0)
        base_lvl1 = weapon_data.get("base_atk_lvl1")
        base_lvl90 = weapon_data.get("base_atk_lvl90")
        passive_desc = weapon_data.get("passive_desc")
        refinements = weapon_data.get("refinements")

        if not wid or not name or self.has_forbidden_placeholder(name):
            missing_fields.append("identity")
        if not base_lvl1 or not base_lvl90 or base_lvl90 < base_lvl1:
            missing_fields.append("base_atk_scaling")
        if rarity > 2 and (not passive_desc or self.has_forbidden_placeholder(passive_desc)):
            missing_fields.append("passive_desc")
        if rarity > 2 and (not isinstance(refinements, list) or len(refinements) != 5):
            missing_fields.append("refinements")

        is_complete = (len(missing_fields) == 0)
        quality_state = KnowledgeQualityState.VERIFIED if is_complete else KnowledgeQualityState.PARTIAL

        return {
            "weapon_id": wid,
            "weapon_name": name,
            "quality_state": quality_state.value,
            "is_complete": is_complete,
            "missing_fields": missing_fields,
        }


# Global singleton
knowledge_contract_service = KnowledgeContractService()
