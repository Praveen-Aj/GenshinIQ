"""
Artifact Optimization Engine (Phase 15).
Pure mathematical evaluation of Roll Value (RV), Crit Value (CV),
custom character stat weights, and candidate loadout optimization
from active GOOD account snapshot inventory.
"""

from typing import Dict, Any, List, Optional, Tuple, Set
import logging
from collections import defaultdict
import itertools

from backend.models.account import AccountArtifactInstance, AccountSnapshot
from backend.services.account_inventory_service import account_inventory_service
from backend.services.game_data_service import game_data_service

logger = logging.getLogger(__name__)

# Canonical maximum tier-4 substat roll values for 5-star artifacts
MAX_SUBSTAT_ROLLS_5STAR = {
    "critRate_": 3.89,
    "critDMG_": 7.77,
    "atk_": 5.83,
    "hp_": 5.83,
    "def_": 7.29,
    "enerRech_": 6.48,
    "eleMas": 23.31,
    "atk": 19.45,
    "hp": 298.75,
    "def": 23.15,
}

def normalize_substat_key(key: str) -> str:
    """Normalize any substat key variation while strictly distinguishing percent from flat stats."""
    if not key:
        return ""
    if key in MAX_SUBSTAT_ROLLS_5STAR:
        return key
    k_lower = key.strip().lower().replace(" ", "")
    if k_lower in ("atk_", "atk%", "attack%"):
        return "atk_"
    if k_lower in ("hp_", "hp%"):
        return "hp_"
    if k_lower in ("def_", "def%"):
        return "def_"
    if k_lower in ("critrate", "critrate_", "crit_rate", "crit_rate%"):
        return "critRate_"
    if k_lower in ("critdmg", "critdmg_", "crit_dmg", "crit_dmg%"):
        return "critDMG_"
    if k_lower in ("enerrech", "enerrech_", "energyrecharge", "er", "er%"):
        return "enerRech_"
    if k_lower in ("elemas", "elementalmastery", "em"):
        return "eleMas"
    if k_lower in ("atk", "flatatk", "flat_atk"):
        return "atk"
    if k_lower in ("hp", "flathp", "flat_hp"):
        return "hp"
    if k_lower in ("def", "flatdef", "flat_def"):
        return "def"
    return key


# Archetype stat weights (0.0 to 1.0)
DEFAULT_STAT_WEIGHTS = {
    "critRate_": 1.0,
    "critDMG_": 1.0,
    "atk_": 0.6,
    "hp_": 0.4,
    "def_": 0.1,
    "enerRech_": 0.5,
    "eleMas": 0.4,
    "atk": 0.2,
    "hp": 0.1,
    "def": 0.05,
}

CHARACTER_STAT_WEIGHTS: Dict[str, Dict[str, float]] = {
    "hu tao": {
        "critRate_": 1.0, "critDMG_": 1.0, "hp_": 0.85, "eleMas": 0.75,
        "atk_": 0.3, "enerRech_": 0.2, "hp": 0.2, "atk": 0.1, "def_": 0.0, "def": 0.0
    },
    "arlecchino": {
        "critRate_": 1.0, "critDMG_": 1.0, "atk_": 0.8, "eleMas": 0.5,
        "enerRech_": 0.3, "atk": 0.25, "hp_": 0.05, "hp": 0.05, "def_": 0.0, "def": 0.0
    },
    "neuvillette": {
        "critRate_": 1.0, "critDMG_": 1.0, "hp_": 0.95, "enerRech_": 0.6,
        "eleMas": 0.2, "hp": 0.25, "atk_": 0.0, "atk": 0.0, "def_": 0.0, "def": 0.0
    },
    "furina": {
        "critRate_": 1.0, "critDMG_": 1.0, "hp_": 0.9, "enerRech_": 0.85,
        "hp": 0.2, "eleMas": 0.1, "atk_": 0.0, "atk": 0.0, "def_": 0.0, "def": 0.0
    },
    "kaedehara kazuha": {
        "eleMas": 1.0, "enerRech_": 0.9, "critRate_": 0.3, "critDMG_": 0.3,
        "atk_": 0.3, "atk": 0.1, "hp_": 0.1, "def_": 0.05, "hp": 0.05, "def": 0.0
    },
    "nahida": {
        "eleMas": 1.0, "critRate_": 0.9, "critDMG_": 0.9, "atk_": 0.4,
        "enerRech_": 0.4, "atk": 0.15, "hp_": 0.05, "def_": 0.0, "hp": 0.05, "def": 0.0
    },
    "raiden shogun": {
        "critRate_": 1.0, "critDMG_": 1.0, "enerRech_": 0.95, "atk_": 0.75,
        "eleMas": 0.3, "atk": 0.2, "hp_": 0.05, "def_": 0.0, "hp": 0.05, "def": 0.0
    },
    "zhongli": {
        "hp_": 1.0, "hp": 0.4, "critRate_": 0.5, "critDMG_": 0.5,
        "enerRech_": 0.4, "atk_": 0.3, "atk": 0.1, "eleMas": 0.0, "def_": 0.0, "def": 0.0
    },
    "bennett": {
        "enerRech_": 1.0, "hp_": 0.8, "hp": 0.3, "critRate_": 0.3,
        "critDMG_": 0.3, "atk_": 0.1, "atk": 0.0, "eleMas": 0.0, "def_": 0.0, "def": 0.0
    },
    "arataki itto": {
        "critRate_": 1.0, "critDMG_": 1.0, "def_": 0.9, "def": 0.25,
        "enerRech_": 0.6, "atk_": 0.2, "atk": 0.1, "eleMas": 0.0, "hp_": 0.0, "hp": 0.0
    }
}


class ArtifactOptimizerService:
    """Evaluates artifact quality, roll values, and computes optimal loadouts."""

    def evaluate_artifact(
        self,
        artifact: Any,
        character_name: Optional[str] = None,
        custom_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Evaluate a single artifact for CV, Roll Value (RV), and effective quality.
        Accepts AccountArtifactInstance or dictionary.
        """
        # Extract fields
        if hasattr(artifact, "substats"):
            substats_raw = artifact.substats
            slot = getattr(artifact, "slot", "flower")
            set_name = getattr(artifact, "canonical_set_name", "Unknown Set")
            main_stat = getattr(artifact, "main_stat_name", "ATK")
            rarity = getattr(artifact, "rarity", 5)
            level = getattr(artifact, "level", 20)
        elif isinstance(artifact, dict):
            substats_raw = artifact.get("substats", [])
            slot = artifact.get("slot", "flower")
            set_name = artifact.get("set_name", artifact.get("canonical_set_name", "Unknown Set"))
            main_stat = artifact.get("main_stat", artifact.get("main_stat_name", "ATK"))
            rarity = artifact.get("rarity", 5)
            level = artifact.get("level", 20)
        else:
            return {"error": "Invalid artifact format"}

        # Resolve weights
        weights = dict(DEFAULT_STAT_WEIGHTS)
        if character_name and character_name.lower() in CHARACTER_STAT_WEIGHTS:
            weights.update(CHARACTER_STAT_WEIGHTS[character_name.lower()])
        if custom_weights:
            weights.update(custom_weights)

        crit_rate = 0.0
        crit_dmg = 0.0
        total_rv = 0.0
        weighted_rv = 0.0
        substat_breakdowns = []

        for sub in substats_raw:
            sub_key = normalize_substat_key(sub.get("key", ""))
            val = float(sub.get("value", 0.0))

            if "critrate" in sub_key.lower():
                crit_rate += val
            elif "critdmg" in sub_key.lower():
                crit_dmg += val

            max_roll = MAX_SUBSTAT_ROLLS_5STAR.get(sub_key, 5.0)
            sub_rv = (val / max_roll) * 100.0 if max_roll > 0 else 0.0
            weight = weights.get(sub_key, 0.2)
            sub_weighted_rv = sub_rv * weight

            total_rv += sub_rv
            weighted_rv += sub_weighted_rv

            substat_breakdowns.append({
                "stat": sub.get("name", sub_key),
                "key": sub_key,
                "value": val,
                "roll_value_pct": round(sub_rv, 1),
                "weight": weight,
                "weighted_rv": round(sub_weighted_rv, 1),
                "estimated_rolls": max(1, round(val / max_roll))
            })

        crit_value = (2.0 * crit_rate) + crit_dmg

        # Tier grading
        if crit_value >= 50.0:
            cv_grade = "Mythic (50+ CV)"
        elif crit_value >= 40.0:
            cv_grade = "Jewel (40-49 CV)"
        elif crit_value >= 30.0:
            cv_grade = "Great (30-39 CV)"
        elif crit_value >= 20.0:
            cv_grade = "Average (20-29 CV)"
        else:
            cv_grade = "Low / Fodder (<20 CV)"

        # Overall RV Rating
        # 540%+ is typical 9-roll threshold
        if total_rv >= 600.0:
            rv_grade = "S-Tier (600%+ RV)"
        elif total_rv >= 500.0:
            rv_grade = "A-Tier (500-599% RV)"
        elif total_rv >= 400.0:
            rv_grade = "B-Tier (400-499% RV)"
        else:
            rv_grade = "C-Tier (<400% RV)"

        return {
            "slot": slot,
            "set_name": set_name,
            "main_stat": main_stat,
            "rarity": rarity,
            "level": level,
            "crit_value": round(crit_value, 1),
            "cv_grade": cv_grade,
            "total_roll_value_pct": round(total_rv, 1),
            "weighted_roll_value_pct": round(weighted_rv, 1),
            "rv_grade": rv_grade,
            "substats": substat_breakdowns
        }

    def get_character_weights(self, character_name: str) -> Dict[str, float]:
        """Return the stat weights configured for a character."""
        name_lower = character_name.lower().strip()
        if name_lower in CHARACTER_STAT_WEIGHTS:
            return dict(CHARACTER_STAT_WEIGHTS[name_lower])
        return dict(DEFAULT_STAT_WEIGHTS)

    def optimize_character_loadout(
        self,
        character_name: str,
        min_er: float = 0.0,
        required_set: Optional[str] = None,
        custom_weights: Optional[Dict[str, float]] = None,
        max_results: int = 3
    ) -> Dict[str, Any]:
        """
        Evaluate account artifacts to discover optimal 5-piece gear loadouts
        for a specific character, respecting set bonuses and stat weight constraints.
        """
        weights = self.get_character_weights(character_name)
        if custom_weights:
            weights.update(custom_weights)

        snapshot: Optional[AccountSnapshot] = account_inventory_service.get_active_snapshot()
        all_artifacts: List[AccountArtifactInstance] = []

        if snapshot and snapshot.artifacts:
            all_artifacts = snapshot.artifacts

        # If no artifacts in snapshot, generate baseline theoretical artifacts
        if len(all_artifacts) < 5:
            return self._generate_theoretical_optimal_build(
                character_name, weights, min_er, required_set
            )

        # Group artifacts by slot
        by_slot: Dict[str, List[AccountArtifactInstance]] = defaultdict(list)
        for art in all_artifacts:
            slot_key = art.slot.lower()
            by_slot[slot_key].append(art)

        # Check that we have at least one artifact per slot
        required_slots = ["flower", "plume", "sands", "goblet", "circlet"]
        missing_slots = [s for s in required_slots if len(by_slot[s]) == 0]
        if missing_slots:
            return self._generate_theoretical_optimal_build(
                character_name, weights, min_er, required_set
            )

        # Score all artifacts individually to prune search space to top 6 per slot
        scored_slots: Dict[str, List[Tuple[float, AccountArtifactInstance]]] = {}
        for slot in required_slots:
            scored = []
            for art in by_slot[slot]:
                eval_res = self.evaluate_artifact(art, character_name, weights)
                score = eval_res["weighted_roll_value_pct"] + (eval_res["crit_value"] * 2.0)
                scored.append((score, art))
            scored.sort(key=lambda x: x[0], reverse=True)
            # Keep top 6 artifacts per slot for combinatorial safety
            scored_slots[slot] = scored[:6]

        # Generate candidate loadouts across the pruned search space
        candidate_loadouts = []
        slot_candidates = [scored_slots[s] for s in required_slots]

        for combo in itertools.product(*slot_candidates):
            arts = [item[1] for item in combo]
            # Check 4pc requirement if specified
            set_counts = defaultdict(int)
            for a in arts:
                set_counts[a.canonical_set_name] += 1

            if required_set:
                if set_counts.get(required_set, 0) < 4:
                    continue

            # Calculate composite metrics
            total_cv = 0.0
            total_weighted_rv = 0.0
            total_er = 100.0  # Base ER 100%

            for a in arts:
                ev = self.evaluate_artifact(a, character_name, weights)
                total_cv += ev["crit_value"]
                total_weighted_rv += ev["weighted_roll_value_pct"]
                for sub in a.substats:
                    k = normalize_substat_key(sub.get("key", ""))
                    if k == "enerRech_":
                        total_er += float(sub.get("value", 0.0))
                if getattr(a, "main_stat_key", "") == "enerRech_":
                    total_er += float(getattr(a, "main_stat_value", 51.8) or 51.8)

            if total_er < min_er:
                continue

            # Set bonus score boost (4pc = +150 pts, 2pc = +50 pts)
            set_score = 0
            active_sets = []
            for sname, cnt in set_counts.items():
                if cnt >= 4:
                    set_score += 150
                    active_sets.append(f"4pc {sname}")
                elif cnt >= 2:
                    set_score += 50
                    active_sets.append(f"2pc {sname}")

            composite_score = total_weighted_rv + (total_cv * 2.5) + set_score

            candidate_loadouts.append({
                "composite_score": round(composite_score, 1),
                "total_crit_value": round(total_cv, 1),
                "total_weighted_rv": round(total_weighted_rv, 1),
                "total_er_pct": round(total_er, 1),
                "active_sets": active_sets,
                "artifacts": [
                    {
                        "slot": a.slot,
                        "set_name": a.canonical_set_name,
                        "main_stat": a.main_stat_name,
                        "level": a.level,
                        "cv": round((2.0 * sum(float(s.get("value", 0)) for s in a.substats if "critrate" in s.get("key", "").lower())) +
                                    sum(float(s.get("value", 0)) for s in a.substats if "critdmg" in s.get("key", "").lower()), 1),
                        "location": a.location or "Bag"
                    }
                    for a in arts
                ]
            })

        candidate_loadouts.sort(key=lambda x: x["composite_score"], reverse=True)
        top_candidates = candidate_loadouts[:max_results]

        # Extract currently equipped build for comparison
        currently_equipped = [a for a in all_artifacts if a.location and a.location.lower() == character_name.lower()]
        current_build_summary = None
        if len(currently_equipped) == 5:
            c_cv = sum(self.evaluate_artifact(a)["crit_value"] for a in currently_equipped)
            c_rv = sum(self.evaluate_artifact(a, character_name, weights)["weighted_roll_value_pct"] for a in currently_equipped)
            c_sets = defaultdict(int)
            for a in currently_equipped:
                c_sets[a.canonical_set_name] += 1
            current_build_summary = {
                "total_crit_value": round(c_cv, 1),
                "total_weighted_rv": round(c_rv, 1),
                "active_sets": [f"{cnt}pc {s}" for s, cnt in c_sets.items() if cnt >= 2]
            }

        # Calculate delta between top candidate and current equipped
        delta = {}
        if current_build_summary and top_candidates:
            best = top_candidates[0]
            delta = {
                "delta_cv": round(best["total_crit_value"] - current_build_summary["total_crit_value"], 1),
                "delta_weighted_rv": round(best["total_weighted_rv"] - current_build_summary["total_weighted_rv"], 1),
                "verdict": "Improvement Available" if best["total_crit_value"] > current_build_summary["total_crit_value"] else "Current Build is Optimal"
            }

        return {
            "character": character_name,
            "has_account_artifacts": True,
            "total_artifacts_evaluated": len(all_artifacts),
            "current_equipped_summary": current_build_summary,
            "optimal_candidates": top_candidates,
            "stat_delta": delta,
            "ai_prompt": f"I optimized artifact loadouts for {character_name}. Best loadout has {top_candidates[0]['total_crit_value'] if top_candidates else 0} CV with {top_candidates[0]['active_sets'] if top_candidates else []}. Should I re-equip?"
        }

    def compare_two_artifacts(
        self,
        artifact_a: Dict[str, Any],
        artifact_b: Dict[str, Any],
        character_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Direct head-to-head comparison of two artifacts."""
        res_a = self.evaluate_artifact(artifact_a, character_name)
        res_b = self.evaluate_artifact(artifact_b, character_name)

        cv_delta = round(res_b["crit_value"] - res_a["crit_value"], 1)
        rv_delta = round(res_b["weighted_roll_value_pct"] - res_a["weighted_roll_value_pct"], 1)

        better = "B" if (rv_delta > 0 or (rv_delta == 0 and cv_delta > 0)) else "A"
        return {
            "artifact_a": res_a,
            "artifact_b": res_b,
            "cv_delta": cv_delta,
            "weighted_rv_delta": rv_delta,
            "recommended": better,
            "summary": f"Artifact {better} is superior by {abs(rv_delta)}% weighted roll value and {abs(cv_delta)} CV."
        }

    def _generate_theoretical_optimal_build(
        self,
        character_name: str,
        weights: Dict[str, float],
        min_er: float,
        required_set: Optional[str]
    ) -> Dict[str, Any]:
        """Fallback when account snapshot has insufficient artifact data."""
        recommended_set = required_set or "Crimson Witch of Flames"
        if "neuvillette" in character_name.lower():
            recommended_set = "Marechaussee Hunter"
        elif "furina" in character_name.lower():
            recommended_set = "Golden Troupe"
        elif "kazuha" in character_name.lower():
            recommended_set = "Viridescent Venerer"

        ideal_artifacts = [
            {"slot": "flower", "set_name": recommended_set, "main_stat": "HP", "cv": 38.8, "level": 20, "location": "Theorycrafting Baseline"},
            {"slot": "plume", "set_name": recommended_set, "main_stat": "ATK", "cv": 42.0, "level": 20, "location": "Theorycrafting Baseline"},
            {"slot": "sands", "set_name": recommended_set, "main_stat": "ATK% / HP% / EM", "cv": 35.0, "level": 20, "location": "Theorycrafting Baseline"},
            {"slot": "goblet", "set_name": "Off-piece", "main_stat": "Elemental DMG%", "cv": 36.4, "level": 20, "location": "Theorycrafting Baseline"},
            {"slot": "circlet", "set_name": recommended_set, "main_stat": "CRIT Rate / CRIT DMG", "cv": 25.0, "level": 20, "location": "Theorycrafting Baseline"}
        ]

        total_cv = sum(a["cv"] for a in ideal_artifacts)
        return {
            "character": character_name,
            "has_account_artifacts": False,
            "notice": "Insufficient account bag artifacts found in active snapshot. Generated theoretical KQM gold standard benchmark build.",
            "optimal_candidates": [
                {
                    "composite_score": 850.0,
                    "total_crit_value": round(total_cv, 1),
                    "total_weighted_rv": 540.0,
                    "total_er_pct": max(130.0, min_er),
                    "active_sets": [f"4pc {recommended_set}"],
                    "artifacts": ideal_artifacts
                }
            ],
            "ai_prompt": f"What domains should I farm to reach the {total_cv} CV benchmark for {character_name} on {recommended_set}?"
        }


artifact_optimizer_service = ArtifactOptimizerService()
