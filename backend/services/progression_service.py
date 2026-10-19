"""
Progression and Farming Calculator Service (Phase 13).
Provides deterministic character ascension, talent level, and resin requirement
calculations with inventory-aware shortfall analysis against account snapshots.
"""

from typing import Dict, Any, List, Optional, Set
import math
from datetime import datetime, timezone

from backend.services.game_data_service import game_data_service
from backend.services.account_inventory_service import account_inventory_service
from backend.services.guide_service import guide_service


ELEMENT_GEMS = {
    "pyro": "Agnidus Agate",
    "hydro": "Varunada Lazurite",
    "anemo": "Vayuda Turquoise",
    "electro": "Vajrada Amethyst",
    "dendro": "Nagadus Emerald",
    "cryo": "Shivada Jade",
    "geo": "Prithiva Topaz",
}

# Cumulative Hero's Wit (20,000 EXP each) and Mora from Level 1 to target level
EXP_BREAKPOINTS = {
    20: {"heros_wit": 6, "mora": 24000},
    40: {"heros_wit": 29, "mora": 116000},
    50: {"heros_wit": 58, "mora": 232000},
    60: {"heros_wit": 101, "mora": 404000},
    70: {"heros_wit": 167, "mora": 668000},
    80: {"heros_wit": 248, "mora": 992000},
    90: {"heros_wit": 419, "mora": 1672500},
}

# Ascension phases (Phase 1 to 6)
ASCENSION_PHASES = [
    {
        "phase": 1, "level": 20, "mora": 20000,
        "gem_tier": "Sliver", "gem_count": 1,
        "boss_count": 0, "specialty_count": 3,
        "common_tier": "Grey", "common_count": 3
    },
    {
        "phase": 2, "level": 40, "mora": 40000,
        "gem_tier": "Fragment", "gem_count": 3,
        "boss_count": 2, "specialty_count": 10,
        "common_tier": "Grey", "common_count": 15
    },
    {
        "phase": 3, "level": 50, "mora": 60000,
        "gem_tier": "Fragment", "gem_count": 6,
        "boss_count": 4, "specialty_count": 20,
        "common_tier": "Green", "common_count": 12
    },
    {
        "phase": 4, "level": 60, "mora": 80000,
        "gem_tier": "Chunk", "gem_count": 3,
        "boss_count": 8, "specialty_count": 30,
        "common_tier": "Green", "common_count": 18
    },
    {
        "phase": 5, "level": 70, "mora": 100000,
        "gem_tier": "Chunk", "gem_count": 6,
        "boss_count": 12, "specialty_count": 45,
        "common_tier": "Blue", "common_count": 12
    },
    {
        "phase": 6, "level": 80, "mora": 120000,
        "gem_tier": "Gemstone", "gem_count": 6,
        "boss_count": 20, "specialty_count": 60,
        "common_tier": "Blue", "common_count": 24
    },
]

# Talent levels from 2 to 10 (per single talent)
TALENT_LEVELS = [
    {"level": 2, "book_tier": "Teachings", "book_count": 3, "common_tier": "Grey", "common_count": 6, "weekly_boss": 0, "crown": 0, "mora": 12500},
    {"level": 3, "book_tier": "Guide", "book_count": 2, "common_tier": "Green", "common_count": 3, "weekly_boss": 0, "crown": 0, "mora": 17500},
    {"level": 4, "book_tier": "Guide", "book_count": 4, "common_tier": "Green", "common_count": 4, "weekly_boss": 0, "crown": 0, "mora": 25000},
    {"level": 5, "book_tier": "Guide", "book_count": 6, "common_tier": "Green", "common_count": 6, "weekly_boss": 0, "crown": 0, "mora": 30000},
    {"level": 6, "book_tier": "Guide", "book_count": 9, "common_tier": "Green", "common_count": 9, "weekly_boss": 0, "crown": 0, "mora": 37500},
    {"level": 7, "book_tier": "Philosophies", "book_count": 4, "common_tier": "Blue", "common_count": 4, "weekly_boss": 1, "crown": 0, "mora": 120000},
    {"level": 8, "book_tier": "Philosophies", "book_count": 6, "common_tier": "Blue", "common_count": 6, "weekly_boss": 1, "crown": 0, "mora": 260000},
    {"level": 9, "book_tier": "Philosophies", "book_count": 12, "common_tier": "Blue", "common_count": 9, "weekly_boss": 2, "crown": 0, "mora": 450000},
    {"level": 10, "book_tier": "Philosophies", "book_count": 16, "common_tier": "Blue", "common_count": 12, "weekly_boss": 2, "crown": 1, "mora": 700000},
]


class ProgressionService:
    """Calculates progression costs, inventory shortfalls, and resin schedules."""

    def calculate_ascension_cost(
        self,
        character_name: str,
        current_level: int = 1,
        target_level: int = 90,
        current_ascension: int = 0,
        target_ascension: int = 6
    ) -> Dict[str, Any]:
        """Calculate deterministic ascension & level up material costs."""
        char = game_data_service.get_character(character_name)
        if not char:
            return {"error": f"Character '{character_name}' not found."}

        # Validation & bounds
        current_level = max(1, min(90, current_level))
        target_level = max(current_level, min(90, target_level))
        current_ascension = max(0, min(6, current_ascension))
        target_ascension = max(current_ascension, min(6, target_ascension))

        # Resolve character-specific material names
        resolved_materials = self._resolve_character_materials(char)
        element_gem = ELEMENT_GEMS.get(char.element.lower(), "Elemental Gem")

        # Accumulate ascension phase costs
        total_mora = 0
        gems = {"Sliver": 0, "Fragment": 0, "Chunk": 0, "Gemstone": 0}
        total_boss_mats = 0
        total_specialties = 0
        common_mats = {"Grey": 0, "Green": 0, "Blue": 0}

        for p in ASCENSION_PHASES:
            if current_ascension < p["phase"] <= target_ascension:
                total_mora += p["mora"]
                gems[p["gem_tier"]] += p["gem_count"]
                total_boss_mats += p["boss_count"]
                total_specialties += p["specialty_count"]
                common_mats[p["common_tier"]] += p["common_count"]

        # Calculate level-up EXP costs (Hero's Wit & Mora)
        current_exp = self._get_exp_cost_up_to(current_level)
        target_exp = self._get_exp_cost_up_to(target_level)
        heros_wit_needed = max(0, target_exp["heros_wit"] - current_exp["heros_wit"])
        exp_mora_needed = max(0, target_exp["mora"] - current_exp["mora"])
        total_mora += exp_mora_needed

        materials_needed = {
            "Mora": total_mora,
            "Hero's Wit": heros_wit_needed,
            f"{element_gem} Sliver": gems["Sliver"],
            f"{element_gem} Fragment": gems["Fragment"],
            f"{element_gem} Chunk": gems["Chunk"],
            f"{element_gem} Gemstone": gems["Gemstone"],
            resolved_materials["boss_material"]: total_boss_mats,
            resolved_materials["specialty"]: total_specialties,
            f"{resolved_materials['common_material']} (Grey)": common_mats["Grey"],
            f"{resolved_materials['common_material']} (Green)": common_mats["Green"],
            f"{resolved_materials['common_material']} (Blue)": common_mats["Blue"],
        }
        # Filter out 0 quantities
        materials_needed = {k: v for k, v in materials_needed.items() if v > 0}

        return {
            "character": char.name,
            "level_transition": f"Lv. {current_level} (A{current_ascension}) -> Lv. {target_level} (A{target_ascension})",
            "materials_needed": materials_needed,
            "total_mora": total_mora,
            "heros_wit": heros_wit_needed,
            "element": char.element,
            "region": char.region or "Teyvat"
        }

    def calculate_talents_cost(
        self,
        character_name: str,
        current_normal: int = 1,
        target_normal: int = 1,
        current_skill: int = 1,
        target_skill: int = 10,
        current_burst: int = 1,
        target_burst: int = 10
    ) -> Dict[str, Any]:
        """Calculate deterministic talent leveling costs for Normal, Skill, and Burst."""
        char = game_data_service.get_character(character_name)
        if not char:
            return {"error": f"Character '{character_name}' not found."}

        resolved_mats = self._resolve_character_materials(char)
        talent_book = resolved_mats["talent_book"]

        talents_plan = [
            ("Normal Attack", max(1, min(10, current_normal)), max(1, min(10, target_normal))),
            ("Elemental Skill", max(1, min(10, current_skill)), max(1, min(10, target_skill))),
            ("Elemental Burst", max(1, min(10, current_burst)), max(1, min(10, target_burst))),
        ]

        total_mora = 0
        books = {"Teachings": 0, "Guide": 0, "Philosophies": 0}
        common_mats = {"Grey": 0, "Green": 0, "Blue": 0}
        total_weekly_boss = 0
        total_crowns = 0

        for name, cur, tgt in talents_plan:
            for t in TALENT_LEVELS:
                if cur < t["level"] <= tgt:
                    total_mora += t["mora"]
                    books[t["book_tier"]] += t["book_count"]
                    common_mats[t["common_tier"]] += t["common_count"]
                    total_weekly_boss += t["weekly_boss"]
                    total_crowns += t["crown"]

        materials_needed = {
            "Mora": total_mora,
            f"Teachings of {talent_book}": books["Teachings"],
            f"Guide to {talent_book}": books["Guide"],
            f"Philosophies of {talent_book}": books["Philosophies"],
            f"{resolved_mats['common_material']} (Grey)": common_mats["Grey"],
            f"{resolved_mats['common_material']} (Green)": common_mats["Green"],
            f"{resolved_mats['common_material']} (Blue)": common_mats["Blue"],
            resolved_mats["weekly_boss"]: total_weekly_boss,
            "Crown of Insight": total_crowns,
        }
        materials_needed = {k: v for k, v in materials_needed.items() if v > 0}

        return {
            "character": char.name,
            "talents_transition": f"Normal: {current_normal}->{target_normal} | Skill: {current_skill}->{target_skill} | Burst: {current_burst}->{target_burst}",
            "materials_needed": materials_needed,
            "total_mora": total_mora,
            "crowns_needed": total_crowns,
            "weekly_boss_material": resolved_mats["weekly_boss"]
        }

    def calculate_full_progression(
        self,
        character_name: str,
        current_level: int = 1,
        target_level: int = 90,
        current_ascension: int = 0,
        target_ascension: int = 6,
        current_talents: Optional[List[int]] = None,
        target_talents: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """Combine ascension and talent costs into a complete progression bill of materials."""
        cur_t = current_talents or [1, 1, 1]
        tgt_t = target_talents or [1, 10, 10]

        asc_cost = self.calculate_ascension_cost(
            character_name, current_level, target_level, current_ascension, target_ascension
        )
        if "error" in asc_cost:
            return asc_cost

        tal_cost = self.calculate_talents_cost(
            character_name, cur_t[0], tgt_t[0], cur_t[1], tgt_t[1], cur_t[2], tgt_t[2]
        )

        # Merge materials
        merged_mats = dict(asc_cost["materials_needed"])
        for mat, count in tal_cost["materials_needed"].items():
            merged_mats[mat] = merged_mats.get(mat, 0) + count

        total_mora = asc_cost["total_mora"] + tal_cost["total_mora"]
        merged_mats["Mora"] = total_mora

        # Calculate estimated Resin requirements
        resin_estimation = self._estimate_resin_requirements(merged_mats)

        return {
            "character": character_name,
            "level_plan": asc_cost["level_transition"],
            "talents_plan": tal_cost["talents_transition"],
            "total_materials_needed": merged_mats,
            "total_mora": total_mora,
            "heros_wit": asc_cost["heros_wit"],
            "resin_estimation": resin_estimation,
            "ai_prompt": f"How should I prioritize farming for {character_name}'s progression to reach {target_level} and talents {tgt_t}?"
        }

    def calculate_inventory_shortfall(
        self,
        character_name: str,
        target_level: int = 90,
        target_ascension: int = 6,
        target_talents: Optional[List[int]] = None
    ) -> Dict[str, Any]:
        """
        Compare full target progression requirements against current account inventory
        from the active GOOD snapshot. Safely handles missing account data.
        """
        char = game_data_service.get_character(character_name)
        if not char:
            return {"error": f"Character '{character_name}' not found."}

        # Try to infer current character level & talents from active account showcase or GOOD bag
        current_level = 1
        current_ascension = 0
        current_talents = [1, 1, 1]
        inventory_bag: Dict[str, int] = {}

        snapshot = account_inventory_service.get_active_snapshot()
        if snapshot:
            # Check characters in snapshot
            owned_char = next(
                (c for c in snapshot.characters if (getattr(c, "canonical_name", None) or getattr(c, "good_key", "")).lower() == char.name.lower()),
                None
            )
            if owned_char:
                current_level = getattr(owned_char, "level", 1) or 1
                current_ascension = getattr(owned_char, "ascension", 0) or 0
                t = getattr(owned_char, "talent_levels", {}) or getattr(owned_char, "talent", {})
                if isinstance(t, dict):
                    current_talents = [t.get("auto", 1), t.get("skill", 1), t.get("burst", 1)]

            # Check materials in snapshot
            for m in snapshot.materials:
                qty = getattr(m, "quantity", 0) or getattr(m, "count", 0)
                inventory_bag[m.good_key.lower()] = qty
                if m.canonical_name:
                    inventory_bag[m.canonical_name.lower()] = qty

        # Compute full required materials from current to target
        progression = self.calculate_full_progression(
            char.name,
            current_level=current_level,
            target_level=target_level,
            current_ascension=current_ascension,
            target_ascension=target_ascension,
            current_talents=current_talents,
            target_talents=target_talents or [1, 10, 10]
        )

        needed = progression["total_materials_needed"]
        shortfall: Dict[str, Dict[str, int]] = {}
        missing_materials: Dict[str, int] = {}

        for mat_name, required_count in needed.items():
            owned_count = inventory_bag.get(mat_name.lower(), 0)
            missing = max(0, required_count - owned_count)
            shortfall[mat_name] = {
                "required": required_count,
                "owned": owned_count,
                "missing": missing,
                "satisfied": missing == 0
            }
            if missing > 0:
                missing_materials[mat_name] = missing

        # Calculate shortfall resin
        shortfall_resin = self._estimate_resin_requirements(missing_materials)

        # Cross reference with today's farming availability
        farming_guide = guide_service.get_farming_guide()
        schedule_status = self._check_farming_availability(missing_materials, farming_guide)

        return {
            "character": char.name,
            "has_account_snapshot": snapshot is not None,
            "current_state": f"Lv. {current_level} (A{current_ascension}) | Talents: {current_talents[0]}/{current_talents[1]}/{current_talents[2]}",
            "target_state": f"Lv. {target_level} (A{target_ascension}) | Talents: {(target_talents or [1, 10, 10])[0]}/{(target_talents or [1, 10, 10])[1]}/{(target_talents or [1, 10, 10])[2]}",
            "shortfall_breakdown": shortfall,
            "missing_materials": missing_materials,
            "shortfall_resin": shortfall_resin,
            "today_farmable_materials": schedule_status["farmable_today"],
            "schedule_notes": schedule_status["notes"],
            "ai_prompt": f"Based on my inventory shortfall, give me a 3-day farming roadmap to max {char.name}."
        }

    # =========================================================================
    # INTERNAL CALCULATIONS & RESOLVERS
    # =========================================================================

    def _resolve_character_materials(self, char: Any) -> Dict[str, str]:
        """Extract canonical material names for character using canonical database types."""
        specialty = "Local Specialty"
        boss_mat = "World Boss Drop"
        common_mat = "Common Material"
        talent_book = "Talent Book"
        weekly_boss = "Weekly Boss Material"

        for m_name in (char.ascension_materials or []):
            mat_obj = game_data_service.get_material(m_name)
            if not mat_obj:
                continue
            m_type = (mat_obj.type or "").lower()
            if "specialty" in m_type:
                specialty = mat_obj.name
            elif "boss" in m_type:
                boss_mat = mat_obj.name
            elif "common" in m_type and common_mat == "Common Material":
                common_mat = mat_obj.name

        for m_name in (char.talent_materials or []):
            mat_obj = game_data_service.get_material(m_name)
            if not mat_obj:
                continue
            m_type = (mat_obj.type or "").lower()
            if "talent" in m_type and "crown" not in mat_obj.name.lower():
                clean_name = (
                    mat_obj.name
                    .replace("Teachings of ", "")
                    .replace("Guide to ", "")
                    .replace("Philosophies of ", "")
                    .strip()
                )
                talent_book = clean_name
            elif "boss" in m_type:
                weekly_boss = mat_obj.name

        return {
            "boss_material": boss_mat,
            "specialty": specialty,
            "common_material": common_mat,
            "talent_book": talent_book,
            "weekly_boss": weekly_boss,
        }

    def _get_exp_cost_up_to(self, level: int) -> Dict[str, int]:
        """Interpolate Hero's Wit and Mora cost up to a target level."""
        if level <= 1:
            return {"heros_wit": 0, "mora": 0}
        for lvl in sorted(EXP_BREAKPOINTS.keys()):
            if level <= lvl:
                return EXP_BREAKPOINTS[lvl]
        return EXP_BREAKPOINTS[90]

    def _estimate_resin_requirements(self, materials: Dict[str, int]) -> Dict[str, Any]:
        """
        Estimate exact resin required to farm missing materials:
        - Boss drops: ~2.5 drops / 40 resin
        - Talent books: ~2.2 blue equivalents / 20 resin (1 Phil = 3 Guides = 9 Teachings)
        - Mora: 60,000 / 20 resin
        - Hero's Wit: 4.5 / 20 resin
        """
        resin_breakdown: Dict[str, int] = {}

        # 1. World Bosses
        for mat, count in materials.items():
            if "Fragment of a Golden Melody" in mat or "Boss" in mat or count in (2, 4, 8, 12, 20, 46):
                if count > 0:
                    runs = math.ceil(count / 2.5)
                    resin_breakdown["World Bosses"] = runs * 40
                break

        # 2. Talent Books
        teachings = 0
        guides = 0
        phils = 0
        for mat, count in materials.items():
            if "Teachings" in mat:
                teachings += count
            elif "Guide" in mat:
                guides += count
            elif "Philosophies" in mat:
                phils += count

        total_guide_equivalents = (teachings / 3.0) + guides + (phils * 3.0)
        if total_guide_equivalents > 0:
            domain_runs = math.ceil(total_guide_equivalents / 2.2)
            resin_breakdown["Talent Domains"] = domain_runs * 20

        # 3. Leylines (Mora & EXP)
        mora = materials.get("Mora", 0)
        if mora > 0:
            resin_breakdown["Mora Leylines"] = math.ceil(mora / 60000) * 20

        heros_wit = materials.get("Hero's Wit", 0)
        if heros_wit > 0:
            resin_breakdown["EXP Leylines"] = math.ceil(heros_wit / 4.5) * 20

        total_resin = sum(resin_breakdown.values())
        # Natural resin regeneration: 180 resin per day
        days_at_180_resin = round(total_resin / 180.0, 1)

        return {
            "total_resin_needed": total_resin,
            "days_of_natural_resin": days_at_180_resin,
            "resin_breakdown": resin_breakdown
        }

    def _check_farming_availability(self, missing_mats: Dict[str, int], farming_guide: Dict[str, Any]) -> Dict[str, Any]:
        """Determine which missing talent books/materials are farmable today."""
        # Days 0=Mon, 1=Tue, 2=Wed, 3=Thu, 4=Fri, 5=Sat, 6=Sun (UTC)
        weekday = datetime.now(timezone.utc).weekday()
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        today_name = day_names[weekday]

        farmable_today = []
        for mat in missing_mats.keys():
            if "Teachings" in mat or "Guide" in mat or "Philosophies" in mat:
                # Sunday: all domains open
                if weekday == 6:
                    farmable_today.append(f"{mat} (Sunday: All Domains Open)")
                else:
                    farmable_today.append(f"{mat} (Check schedule)")

        return {
            "farmable_today": farmable_today,
            "today_weekday": today_name,
            "notes": "Sunday permits unrestricted talent and weapon domain farming across all regions." if weekday == 6 else f"Today is {today_name}. Farm matching regional domains."
        }


progression_service = ProgressionService()
