"""
GenshinIQ — Guide Domain Service (Phase 12)
Orchestrates the Structured Visual Knowledge Library:
- Characters, Weapons, Artifacts, Teams, Mechanics, and Farming.
- Strict taxonomy: CURATED_CHARACTER_GUIDE vs GENERIC_FALLBACK vs MISSING.
- Strict consumer sanitization: zero source IDs, authority tiers, or internal pipeline jargon exposed.
- Deterministic stat derivations via stat_engine.
"""

from datetime import datetime, timezone
import json
import logging
from pathlib import Path
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from backend.services.game_data_service import game_data_service
from backend.services.encyclopedia_service import encyclopedia_service
from backend.services.stat_engine import stat_engine_service as stat_engine

logger = logging.getLogger(__name__)


class GuideService:
    """Centralized service providing structured, visual, consumer-ready guide experiences."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(".")
        self.knowledge_dir = self.base_dir / "data" / "knowledge"
        self._curated_chars = {
            "kaedehara kazuha", "furina", "arlecchino", "mavuika",
            "raiden shogun", "nahida", "zhongli", "yelan",
            "hu tao", "neuvillette", "alhaitham", "xiangling",
            "xingqiu", "bennett", "ganyu"
        }
        self._mechanics_cache: Optional[List[Dict[str, Any]]] = None
        self._teams_cache: Optional[List[Dict[str, Any]]] = None
        self._farming_cache: Optional[Dict[str, Any]] = None

    # =========================================================================
    # SUMMARY & OVERVIEW
    # =========================================================================

    def get_guides_summary(self) -> Dict[str, Any]:
        """Return high-level summary metrics of all available guides."""
        chars = game_data_service.list_characters()
        weapons = game_data_service.list_weapons()
        artifacts = game_data_service.list_artifact_sets()
        mechanics = self._get_all_mechanics()
        teams = self._get_all_teams()

        curated_chars_count = len([c for c in chars if c.name.lower() in self._curated_chars])
        fallback_chars_count = len(chars) - curated_chars_count

        return {
            "total_guides": len(chars) + len(weapons) + len(artifacts) + len(mechanics) + len(teams) + 1,
            "categories": {
                "characters": {
                    "total": len(chars),
                    "curated": curated_chars_count,
                    "baseline": fallback_chars_count,
                    "taxonomy": {
                        "curated_badge": "✨ Curated Theorycrafting",
                        "baseline_badge": "ℹ️ Archetype Baseline"
                    }
                },
                "weapons": {
                    "total": len(weapons),
                    "curated": len(weapons),
                    "scaling_engine": "Deterministic Hoyoverse Curve Evaluation"
                },
                "artifacts": {
                    "total": len(artifacts),
                    "curated": len(artifacts)
                },
                "teams": {
                    "total": len(teams),
                    "curated": len(teams)
                },
                "mechanics": {
                    "total": len(mechanics),
                    "curated": len(mechanics)
                },
                "farming": {
                    "total": 1,
                    "schedules": "Daily Talent Books & Weapon Ascension Rotations"
                }
            },
            "taxonomy_rules": {
                "never_masquerade_fallback": True,
                "zero_source_leakage": True
            }
        }

    # =========================================================================
    # FILTERABLE GUIDE LISTING
    # =========================================================================

    def list_guides(
        self,
        category: str = "all",
        q: Optional[str] = None,
        element: Optional[str] = None,
        weapon_type: Optional[str] = None,
        rarity: Optional[int] = None,
        role: Optional[str] = None,
        availability: Optional[str] = None,
        owned_character_names: Optional[Set[str]] = None,
        owned_only: bool = False,
        sort: str = "curated_first",
    ) -> List[Dict[str, Any]]:
        """List guide index items with multi-attribute filtering and ranking."""
        items: List[Dict[str, Any]] = []
        q_norm = q.strip().lower() if q else None

        # 1. Characters
        if category in ("all", "characters"):
            for char in game_data_service.list_characters():
                c_name = char.name
                c_name_lower = c_name.lower()
                is_curated = c_name_lower in self._curated_chars
                is_owned = owned_character_names is not None and (c_name_lower in owned_character_names or any(c_name_lower in o.lower() for o in owned_character_names))

                if owned_only and not is_owned:
                    continue
                if element and char.element.lower() != element.lower():
                    continue
                if weapon_type and char.weapon_type.lower() != weapon_type.lower():
                    continue
                if rarity and char.rarity != rarity:
                    continue
                if availability == "curated" and not is_curated:
                    continue
                if availability == "baseline" and is_curated:
                    continue

                # Query match
                if q_norm:
                    matches = (
                        q_norm in c_name_lower or
                        q_norm in char.element.lower() or
                        q_norm in char.weapon_type.lower() or
                        (char.role and q_norm in char.role.lower())
                    )
                    if not matches:
                        continue

                items.append({
                    "id": f"char_{char.id or c_name_lower.replace(' ', '_')}",
                    "entity_id": char.id or c_name,
                    "category": "characters",
                    "title": c_name,
                    "subtitle": f"{char.rarity}★ {char.element} {char.weapon_type}",
                    "element": char.element,
                    "weapon_type": char.weapon_type,
                    "rarity": char.rarity,
                    "role": getattr(char, "role", None) or ("Main DPS" if char.rarity == 5 else "Support"),
                    "icon_url": getattr(char, "icon", None) or f"https://enka.network/ui/UI_AvatarIcon_{c_name.replace(' ', '')}.png",
                    "guide_type": "CURATED_CHARACTER_GUIDE" if is_curated else "GENERIC_FALLBACK",
                    "guide_badge": "✨ Curated Theorycrafting" if is_curated else "ℹ️ Archetype Baseline",
                    "is_owned": is_owned,
                    "summary": f"Complete guide: talent priority, BiS weapons, artifact loadout, and top team synergies."
                })

        # 2. Weapons
        if category in ("all", "weapons") and not owned_only:
            for wep in game_data_service.list_weapons():
                w_name = wep.name
                w_name_lower = w_name.lower()

                if weapon_type and wep.weapon_type.lower() != weapon_type.lower():
                    continue
                if rarity and wep.rarity != rarity:
                    continue

                if q_norm:
                    matches = (
                        q_norm in w_name_lower or
                        q_norm in wep.weapon_type.lower() or
                        q_norm in (wep.sub_stat_type or "").lower() or
                        q_norm in (getattr(wep, "passive_desc", None) or "").lower()
                    )
                    if not matches:
                        continue

                items.append({
                    "id": f"wep_{wep.id or w_name_lower.replace(' ', '_')}",
                    "entity_id": wep.id or w_name,
                    "category": "weapons",
                    "title": w_name,
                    "subtitle": f"{wep.rarity}★ {wep.weapon_type}",
                    "weapon_type": wep.weapon_type,
                    "rarity": wep.rarity,
                    "base_atk": wep.base_atk_lvl90,
                    "secondary_stat": wep.sub_stat_type,
                    "icon_url": getattr(wep, "icon", None) or f"https://enka.network/ui/UI_EquipIcon_{wep.weapon_type}_{w_name.replace(' ', '')}.png",
                    "guide_type": "CURATED_WEAPON_GUIDE",
                    "guide_badge": "⚔️ Weapon Guide",
                    "summary": f"Lv. 90 Base ATK: {wep.base_atk_lvl90} | {wep.sub_stat_type or 'Stat stick'} | Passives & Refinement scaling."
                })

        # 3. Artifact Sets
        if category in ("all", "artifacts") and not owned_only:
            for art in game_data_service.list_artifact_sets():
                a_name = art.name
                a_name_lower = a_name.lower()

                if rarity and art.max_rarity != rarity:
                    continue

                if q_norm:
                    matches = (
                        q_norm in a_name_lower or
                        q_norm in (art.bonus_2pc or "").lower() or
                        q_norm in (art.bonus_4pc or "").lower()
                    )
                    if not matches:
                        continue

                items.append({
                    "id": f"art_{art.id or a_name_lower.replace(' ', '_')}",
                    "entity_id": art.id or a_name,
                    "category": "artifacts",
                    "title": a_name,
                    "subtitle": f"{art.max_rarity}★ Artifact Set",
                    "rarity": art.max_rarity,
                    "icon_url": getattr(art, "icon", None) or "https://enka.network/ui/UI_RelicIcon_15001_4.png",
                    "guide_type": "CURATED_ARTIFACT_GUIDE",
                    "guide_badge": "🛡️ Artifact Set",
                    "summary": f"2-pc: {(art.bonus_2pc or '')[:70]}... | 4-pc: {(art.bonus_4pc or '')[:70]}..." if art.bonus_4pc else f"2-pc: {art.bonus_2pc}"
                })

        # 4. Team Archetypes
        if category in ("all", "teams") and not owned_only:
            for team in self._get_all_teams():
                t_name = team["title"]
                if q_norm and q_norm not in t_name.lower() and q_norm not in team["summary"].lower():
                    continue

                items.append({
                    "id": team["id"],
                    "entity_id": team["slug"],
                    "category": "teams",
                    "title": t_name,
                    "subtitle": team["archetype"],
                    "rarity": 5,
                    "guide_type": "CURATED_TEAM_GUIDE",
                    "guide_badge": "👥 Team Archetype",
                    "icon_url": "https://enka.network/ui/UI_Icon_Element_Pyro.png",
                    "summary": team["summary"]
                })

        # 5. Game Mechanics
        if category in ("all", "mechanics") and not owned_only:
            for mech in self._get_all_mechanics():
                m_name = mech["title"]
                if q_norm and q_norm not in m_name.lower() and q_norm not in mech["summary"].lower():
                    continue

                items.append({
                    "id": mech["id"],
                    "entity_id": mech["slug"],
                    "category": "mechanics",
                    "title": m_name,
                    "subtitle": mech["topic"],
                    "rarity": 5,
                    "guide_type": "CURATED_MECHANICS_GUIDE",
                    "guide_badge": "⚙️ Game Mechanics",
                    "icon_url": "https://enka.network/ui/UI_Icon_Element_Anemo.png",
                    "summary": mech["summary"]
                })

        # 6. Daily Farming
        if category in ("all", "farming") and not owned_only:
            farming_item = {
                "id": "guide_daily_farming_rotation",
                "entity_id": "daily_farming",
                "category": "farming",
                "title": "Daily Domain Farming Schedule",
                "subtitle": "Talent Books & Weapon Ascension Materials",
                "rarity": 5,
                "guide_type": "CURATED_FARMING_GUIDE",
                "guide_badge": "📅 Farming Rotation",
                "icon_url": "https://enka.network/ui/UI_ItemIcon_104319.png",
                "summary": "Full weekday rotation schedule for all regions (Mondstadt, Liyue, Inazuma, Sumeru, Fontaine, Natlan)."
            }
            if not q_norm or any(k in q_norm for k in ["farm", "domain", "schedule", "talent", "weapon", "rotation", "today"]):
                items.append(farming_item)

        # Sorting logic
        if sort == "curated_first":
            items.sort(key=lambda x: (
                0 if x["guide_type"] == "CURATED_CHARACTER_GUIDE" else
                1 if "CURATED" in x["guide_type"] else
                2,
                -x.get("rarity", 0),
                x["title"]
            ))
        elif sort == "rarity_desc":
            items.sort(key=lambda x: (-x.get("rarity", 0), x["title"]))
        elif sort == "name":
            items.sort(key=lambda x: x["title"])

        return items

    # =========================================================================
    # CHARACTER GUIDE VIEW (15 Visual Sections)
    # =========================================================================

    def get_character_guide(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Return structured 15-section visual character guide."""
        char = game_data_service.get_character(name_or_id)
        if not char:
            return None

        # Build guide via encyclopedia service
        encyclopedia_guide = encyclopedia_service.get_character_build_guide(char.name)
        if not encyclopedia_guide:
            return None

        name = char.name
        is_curated = name.lower() in self._curated_chars

        # Clean sanitized structure
        return {
            "character_name": name,
            "element": char.element,
            "weapon_type": char.weapon_type,
            "rarity": char.rarity,
            "icon_url": getattr(char, "icon", None) or f"https://enka.network/ui/UI_AvatarIcon_{name.replace(' ', '')}.png",
            "guide_type": "CURATED_CHARACTER_GUIDE" if is_curated else "GENERIC_FALLBACK",
            "guide_badge": "✨ Curated Theorycrafting" if is_curated else "ℹ️ Archetype Baseline",
            "provenance_note": (
                "Hand-curated weapon tiering, artifact priorities, and team archetypes."
                if is_curated else
                "Baseline archetype recommendations derived from canonical character element and scaling."
            ),
            # 1. Overview
            "overview": encyclopedia_guide.get("overview", f"{name} is a {char.rarity}★ {char.element} {char.weapon_type} character."),
            # 2. Role
            "role": encyclopedia_guide.get("role", "Sub-DPS / Support"),
            # 3. How the character works
            "how_it_works": encyclopedia_guide.get("playstyle", f"Focuses on applying {char.element} and executing consistent skill rotations."),
            # 4. Strengths & Caveats
            "strengths": encyclopedia_guide.get("strengths", [f"Strong {char.element} application", "High team synergy"]),
            "caveats": encyclopedia_guide.get("caveats", ["Requires appropriate Energy Recharge", "Rotation timing"]),
            # 5. Talent priorities
            "talent_priority": encyclopedia_guide.get("talent_priority", "Burst >= Skill > Normal Attack"),
            "talents_breakdown": [
                {"name": "Normal Attack", "role": "Normal & Charged Attacks", "importance": "Low" if char.weapon_type != "Bow" else "Situational"},
                {"name": "Elemental Skill", "role": "Skill generation & core effect", "importance": "High"},
                {"name": "Elemental Burst", "role": "High impact Burst ability", "importance": "Primary"}
            ],
            # 6. Build Recommendations
            "build_overview": "Maximize primary scalings while hitting Energy Recharge thresholds for reliable burst uptime.",
            # 7. Weapons
            "weapons": encyclopedia_guide.get("recommended_weapons") or encyclopedia_guide.get("weapons", []),
            # 8. Artifacts
            "artifacts": encyclopedia_guide.get("recommended_artifacts") or encyclopedia_guide.get("artifacts", []),
            # 9. Main Stats
            "main_stats": encyclopedia_guide.get("main_stats", {
                "sands": "ATK% or Energy Recharge",
                "goblet": f"{char.element} DMG Bonus",
                "circlet": "CRIT Rate or CRIT DMG"
            }),
            # 10. Substats
            "substats": encyclopedia_guide.get("substat_priorities") or encyclopedia_guide.get("substats", ["CRIT Rate / CRIT DMG", "Energy Recharge", "ATK%", "Elemental Mastery"]),
            # 11. Energy & Rotation Considerations
            "energy_benchmarks": encyclopedia_guide.get("stat_benchmarks", {"er": "140% - 160%", "crit_ratio": "60% / 120%"}),
            # 12. Synergistic Teams
            "teams": encyclopedia_guide.get("teams") or encyclopedia_guide.get("team_comps", []),
            # 13. Constellation Evaluations
            "constellations_summary": [
                {"tier": "C1", "name": "Initial Upgrade", "verdict": "Quality of life or slight damage boost."},
                {"tier": "C2", "name": "Key Spike", "verdict": "Major team utility or massive personal damage increase."},
                {"tier": "C4", "name": "Team Buff", "verdict": "Defensive or energy buff for active party members."},
                {"tier": "C6", "name": "Apex Potential", "verdict": "Unlocks on-field carry potential or transformative scaling."}
            ],
            # 14. Farming & Materials
            "farming": encyclopedia_guide.get("farming", {}),
            # 15. Contextual AI Actions
            "ai_actions": [
                {"label": "✨ Review My Build", "prompt": f"Review my {name} build based on my account inventory and tell me what to improve."},
                {"label": "✨ Compare Weapons", "prompt": f"What is the best weapon for {name} among the weapons I own?"},
                {"label": "✨ Find Best Teams", "prompt": f"What are the best teams for {name} using characters available on my account?"},
                {"label": "✨ Optimize Artifacts", "prompt": f"How should I optimize artifact substats and main stats for {name}?"}
            ]
        }

    # =========================================================================
    # WEAPON GUIDE VIEW (Deterministic Curves)
    # =========================================================================

    def get_weapon_guide(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Return structured weapon guide with exact deterministic mathematical curves."""
        wep = game_data_service.get_weapon(name_or_id)
        if not wep:
            return None

        # Calculate exact Lv 1 and Lv 90 stats via encyclopedia_service
        scaling_lv1 = encyclopedia_service.get_weapon_scaling(wep.name, level=1, ascension=0, refinement=1)
        scaling_lv90_r1 = encyclopedia_service.get_weapon_scaling(wep.name, level=90, ascension=6, refinement=1)
        scaling_lv90_r5 = encyclopedia_service.get_weapon_scaling(wep.name, level=90, ascension=6, refinement=5)

        # Infer notable users based on weapon type and secondary stat
        users = self._infer_weapon_users(wep)

        return {
            "name": wep.name,
            "weapon_type": wep.weapon_type,
            "rarity": wep.rarity,
            "icon_url": getattr(wep, "icon", None) or f"https://enka.network/ui/UI_EquipIcon_{wep.weapon_type}_{wep.name.replace(' ', '')}.png",
            "guide_badge": f"{wep.rarity}★ Weapon Guide",
            "base_atk_lv1": scaling_lv1.get("base_atk", wep.base_atk_lvl1),
            "base_atk_lv90": scaling_lv90_r1.get("base_atk", wep.base_atk_lvl90),
            "sub_stat_type": wep.sub_stat_type,
            "sub_stat_lv1": scaling_lv1.get("sub_stat_formatted", "—"),
            "sub_stat_lv90": scaling_lv90_r1.get("sub_stat_formatted", "—"),
            "passive_name": wep.passive_name or "Weapon Affinity",
            "passive_desc": wep.passive_desc or "Increases combat stats based on refinement tier.",
            "refinement_scaling": {
                "r1": scaling_lv90_r1.get("static_passives", {}),
                "r5": scaling_lv90_r5.get("static_passives", {})
            },
            "notable_users": users,
            "f2p_context": (
                "Available from standard gacha or regional craftable forging."
                if wep.rarity <= 4 else
                "Limited 5★ weapon banner; high investment ceiling."
            ),
            "alternatives": self._suggest_weapon_alternatives(wep),
            "ai_actions": [
                {"label": "✨ Who Should Equip This?", "prompt": f"Which of my characters gets the highest value from {wep.name}?"},
                {"label": "✨ Compare With Alternatives", "prompt": f"Compare {wep.name} against other {wep.weapon_type} options in my account."}
            ]
        }

    # =========================================================================
    # ARTIFACT SET GUIDE VIEW
    # =========================================================================

    def get_artifact_guide(self, name_or_id: str) -> Optional[Dict[str, Any]]:
        """Return structured artifact set guide."""
        art = game_data_service.get_artifact_set(name_or_id)
        if not art:
            return None

        # Find notable characters that recommend this set
        users = self._infer_artifact_users(art.name)

        return {
            "name": art.name,
            "rarity": art.max_rarity,
            "icon_url": getattr(art, "icon", None) or "https://enka.network/ui/UI_RelicIcon_15001_4.png",
            "bonus_2pc": art.bonus_2pc,
            "bonus_4pc": art.bonus_4pc,
            "notable_users": users,
            "recommended_roles": "Burst DPS / Sub-DPS / Support",
            "domain_info": {
                "domain_name": "Artifact Reliquary Domain",
                "days_available": "Always Available (Every Day)"
            },
            "stat_priorities": {
                "sands": "ATK% / HP% / Energy Recharge",
                "goblet": "Elemental DMG Bonus",
                "circlet": "CRIT Rate or CRIT DMG"
            },
            "ai_actions": [
                {"label": "✨ Check My Artifact Inventory", "prompt": f"Do I have a good 4-piece set of {art.name} in my account inventory?"},
                {"label": "✨ Who Should Use This Set?", "prompt": f"Which of my characters should I equip {art.name} on?"}
            ]
        }

    # =========================================================================
    # MECHANICS GUIDE VIEW
    # =========================================================================

    def get_mechanics_guide(self, slug_or_id: str) -> Optional[Dict[str, Any]]:
        """Return structured visual breakdown of game mechanics."""
        all_mech = self._get_all_mechanics()
        slug_norm = slug_or_id.lower().replace("-", "_").replace(" ", "_")
        target = next((m for m in all_mech if m["slug"] == slug_norm or m["id"] == slug_or_id or slug_norm in m["slug"]), None)
        if not target:
            return None

        return {
            "title": target["title"],
            "slug": target["slug"],
            "topic": target["topic"],
            "summary": target["summary"],
            "visual_sections": target.get("visual_sections", []),
            "key_formulas": target.get("key_formulas", []),
            "takeaways": target.get("takeaways", []),
            "ai_actions": [
                {"label": "✨ Explain for My Characters", "prompt": f"Explain {target['title']} and how it applies to my team compositions."},
                {"label": "✨ Calculate Stats", "prompt": f"How do I maximize my damage using {target['title']} mechanics?"}
            ]
        }

    # =========================================================================
    # TEAM ARCHETYPES GUIDE VIEW
    # =========================================================================

    def get_team_guide(self, slug_or_id: str) -> Optional[Dict[str, Any]]:
        """Return structured team archetype guide."""
        teams = self._get_all_teams()
        slug_norm = slug_or_id.lower().replace("-", "_").replace(" ", "_")
        target = next((t for t in teams if t["slug"] == slug_norm or t["id"] == slug_or_id or slug_norm in t["slug"]), None)
        if not target:
            return None

        return {
            "title": target["title"],
            "slug": target["slug"],
            "archetype": target["archetype"],
            "summary": target["summary"],
            "core_characters": target["core_characters"],
            "rotation_steps": target["rotation_steps"],
            "variants": target["variants"],
            "ai_actions": [
                {"label": "✨ Build This Team From My Account", "prompt": f"Can I build a {target['title']} team from my account characters? What substitutions should I use?"},
                {"label": "✨ Explain Rotation", "prompt": f"Step by step, what is the exact rotation for {target['title']}?"}
            ]
        }

    # =========================================================================
    # DAILY FARMING ROTATION GUIDE VIEW
    # =========================================================================

    def get_farming_guide(self) -> Dict[str, Any]:
        """Return comprehensive weekday domain farming rotation planner."""
        return {
            "title": "Teyvat Daily Domain Farming Schedule",
            "subtitle": "Talent Books & Weapon Ascension Materials by Region & Weekday",
            "rotations": [
                {
                    "days": "Monday & Thursday (and Sunday)",
                    "domains": [
                        {"region": "Mondstadt", "talent_book": "Freedom", "characters": ["Klee", "Sucrose", "Diona", "Tartaglia", "Amber", "Barbara", "Aloy"]},
                        {"region": "Liyue", "talent_book": "Prosperity", "characters": ["Keqing", "Ningguang", "Qiqi", "Shenhe", "Xiao", "Yelan"]},
                        {"region": "Inazuma", "talent_book": "Transience", "characters": ["Yoimiya", "Thoma", "Kokomi", "Heizou", "Kirara"]},
                        {"region": "Sumeru", "talent_book": "Admonition", "characters": ["Tighnari", "Candace", "Cyno", "Faruzan"]},
                        {"region": "Fontaine", "talent_book": "Equity", "characters": ["Lyney", "Neuvillette", "Navia", "Sigewinne"]},
                        {"region": "Natlan", "talent_book": "Contention", "characters": ["Mualani", "Xilonen", "Chasca"]}
                    ]
                },
                {
                    "days": "Tuesday & Friday (and Sunday)",
                    "domains": [
                        {"region": "Mondstadt", "talent_book": "Resistance", "characters": ["Jean", "Diluc", "Mona", "Bennett", "Noelle", "Razor", "Eula"]},
                        {"region": "Liyue", "talent_book": "Diligence", "characters": ["Xiangling", "Chongyun", "Ganyu", "Hu Tao", "Kazuha", "Yun Jin", "Yaoyao"]},
                        {"region": "Inazuma", "talent_book": "Elegance", "characters": ["Ayaka", "Ayato", "Sara", "Itto", "Shinobu"]},
                        {"region": "Sumeru", "talent_book": "Ingenuity", "characters": ["Dori", "Nahida", "Layla", "Alhaitham", "Kaveh"]},
                        {"region": "Fontaine", "talent_book": "Justice", "characters": ["Freminet", "Wriothesley", "Furina", "Charlotte", "Clorinde"]},
                        {"region": "Natlan", "talent_book": "Kindling", "characters": ["Kinich", "Ororon", "Mavuika"]}
                    ]
                },
                {
                    "days": "Wednesday & Saturday (and Sunday)",
                    "domains": [
                        {"region": "Mondstadt", "talent_book": "Ballad", "characters": ["Venti", "Kaeya", "Lisa", "Rosaria", "Albedo", "Fischl", "Mika"]},
                        {"region": "Liyue", "talent_book": "Gold", "characters": ["Beidou", "Xingqiu", "Zhongli", "Xinyan", "Yanfei", "Baizhu", "Xianyun", "Gaming"]},
                        {"region": "Inazuma", "talent_book": "Light", "characters": ["Raiden Shogun", "Sayu", "Yae Miko", "Gorou"]},
                        {"region": "Sumeru", "talent_book": "Praxis", "characters": ["Collei", "Nilou", "Dehya", "Wanderer", "Sethos"]},
                        {"region": "Fontaine", "talent_book": "Order", "characters": ["Lynette", "Chevreuse", "Chiori", "Arlecchino", "Emilie"]},
                        {"region": "Natlan", "talent_book": "Conflict", "characters": ["Kachina", "Citlali", "Iansan"]}
                    ]
                }
            ],
            "sunday_rule": "On Sunday, all talent book and weapon material domains are available simultaneously.",
            "ai_actions": [
                {"label": "✨ Plan Today's Farming", "prompt": "Based on my account characters and builds, what talent books and weapon materials should I farm today?"}
            ]
        }

    # =========================================================================
    # INTERNAL HELPERS
    # =========================================================================

    def _infer_weapon_users(self, wep: Any) -> List[str]:
        """Infer notable character users for a weapon."""
        name = wep.name
        w_type = wep.weapon_type
        stat = (wep.secondary_stat or "").lower()

        if "Mistsplitter" in name:
            return ["Kamisato Ayaka", "Keqing", "Alhaitham", "Bennett"]
        if "Freedom-Sworn" in name:
            return ["Kaedehara Kazuha", "Kuki Shinobu", "Jean"]
        if "Staff of Homa" in name:
            return ["Hu Tao", "Zhongli", "Raiden Shogun", "Xiangling"]
        if "The Catch" in name:
            return ["Raiden Shogun", "Xiangling"]
        if "Favonius" in name:
            return ["Supports needing team energy recharge"]
        if "Golden Troupe" in name:
            return ["Furina", "Fischl", "Yae Miko"]

        # Default by weapon type
        type_users = {
            "Sword": ["Kaedehara Kazuha", "Furina", "Xingqiu", "Bennett"],
            "Claymore": ["Mavuika", "Navia", "Arataki Itto", "Diluc"],
            "Polearm": ["Arlecchino", "Raiden Shogun", "Xiangling", "Zhongli"],
            "Bow": ["Yelan", "Ganyu", "Fischl", "Tartaglia"],
            "Catalyst": ["Neuvillette", "Nahida", "Wriothesley", "Yae Miko"],
        }
        return type_users.get(w_type, ["Flexible DPS / Support users"])

    def _suggest_weapon_alternatives(self, wep: Any) -> List[str]:
        """Suggest alternatives in same weapon category."""
        alts = {
            "Sword": ["Favonius Sword", "Iron Sting", "Fleuve Cendre Ferryman", "Xiphos' Moonlight"],
            "Claymore": ["Serpent Spine", "Favonius Greatsword", "Earth Shaker"],
            "Polearm": ["The Catch", "Favonius Lance", "Dragon's Bane", "White Tassel"],
            "Bow": ["Favonius Warbow", "The Stringless", "Fading Twilight"],
            "Catalyst": ["The Widsith", "Sacrificial Fragments", "Prototype Amber"]
        }
        return [a for a in alts.get(wep.weapon_type, []) if a != wep.name]

    def _infer_artifact_users(self, set_name: str) -> List[str]:
        """Infer notable users of an artifact set."""
        name_lower = set_name.lower()
        if "viridescent" in name_lower:
            return ["Kaedehara Kazuha", "Venti", "Sucrose", "Jean", "Xianyun"]
        if "golden troupe" in name_lower:
            return ["Furina", "Fischl", "Yae Miko", "Chiori"]
        if "harmonic whimsy" in name_lower:
            return ["Arlecchino", "Clorinde"]
        if "obsidian codex" in name_lower:
            return ["Mavuika", "Kinich", "Mualani", "Chasca"]
        if "emblem" in name_lower:
            return ["Raiden Shogun", "Xiangling", "Xingqiu", "Yelan", "Beidou"]
        if "deepwood" in name_lower:
            return ["Nahida", "Collei", "Baizhu", "Yaoyao"]
        if "marechaussee" in name_lower:
            return ["Neuvillette", "Wriothesley", "Gaming", "Xiao"]
        if "noblesse" in name_lower:
            return ["Bennett", "Mona", "Diona", "Mika"]
        return ["DPS / Support characters matching elemental synergy"]

    def _get_all_teams(self) -> List[Dict[str, Any]]:
        """Return structured team archetypes."""
        if self._teams_cache is None:
            self._teams_cache = [
                {
                    "id": "team_national",
                    "slug": "national",
                    "title": "The National Team",
                    "archetype": "Vaporize / Multi-Reaction Driver",
                    "summary": "High damage floor utilizing Bennett's massive flat ATK buff, Xiangling's Pyronado snapshot, and Xingqiu's off-field Hydro.",
                    "core_characters": ["Xiangling", "Bennett", "Xingqiu", "Kaedehara Kazuha"],
                    "rotation_steps": [
                        "1. Bennett Burst (Q) to trigger Inspiration Field.",
                        "2. Kazuha Skill/Burst (E/Q) to double-swirl Pyro and Hydro.",
                        "3. Xingqiu Burst (Q) -> Skill (E) for continuous Hydro swords.",
                        "4. Xiangling Burst (Q) -> Skill (E) to snapshot Bennett's buff and trigger continuous Vaporize."
                    ],
                    "variants": ["Raiden National (Rational)", "International (with Tartaglia)", "Funerational (with Hu Tao)"]
                },
                {
                    "id": "team_hyperbloom",
                    "slug": "hyperbloom",
                    "title": "Quickbloom & Hyperbloom",
                    "archetype": "Transformative Reaction Driver",
                    "summary": "High floor, low investment reaction team combining Dendro Cores with fast Electro triggers.",
                    "core_characters": ["Nahida", "Xingqiu", "Kuki Shinobu", "Alhaitham"],
                    "rotation_steps": [
                        "1. Nahida Skill (E) -> Burst (Q) for Tri-Karma purification and EM buff.",
                        "2. Xingqiu Burst (Q) -> Skill (E) for Hydro aura.",
                        "3. Kuki Shinobu Skill (E) full EM build to trigger Hyperbloom homing missiles.",
                        "4. Alhaitham Normal/Chisel attacks on-field for continuous Dendro driving."
                    ],
                    "variants": ["Double Hydro Hyperbloom (Yelan + Xingqiu)", "Raiden EM Hyperbloom", "Neuvillette Hyperbloom"]
                },
                {
                    "id": "team_furina_hypercarry",
                    "slug": "furina_hypercarry",
                    "title": "Universal Fanfare Hypercarry",
                    "archetype": "Universal Buff & HP Fluctuation",
                    "summary": "Maximizes team-wide Fanfare damage bonuses using Furina's Salon Solitaire and a party-wide healer.",
                    "core_characters": ["Furina", "Neuvillette", "Kaedehara Kazuha", "Baizhu"],
                    "rotation_steps": [
                        "1. Furina Skill (E) -> Burst (Q) to begin HP drain and Fanfare accumulation.",
                        "2. Team healer Skill/Burst (Xianyun / Baizhu / Jean) to trigger instant max Fanfare.",
                        "3. Kazuha Swirl to shred elemental resistance.",
                        "4. Main DPS attacks with +75% universal DMG bonus."
                    ],
                    "variants": ["Hu Tao + Furina + Yelan + Xianyun", "Xiao + Furina + Faruzan + Xianyun", "Navia + Furina + Zhongli + Bennett"]
                },
                {
                    "id": "team_freeze",
                    "slug": "freeze",
                    "title": "Morgana & Blizzard Freeze",
                    "archetype": "Crowd Control & 100% CRIT Freeze",
                    "summary": "Locks mobs in perpetual frozen state, granting +40% CRIT Rate via Blizzard Strayer with zero knockback.",
                    "core_characters": ["Kamisato Ayaka", "Shenhe", "Kaedehara Kazuha", "Kokomi"],
                    "rotation_steps": [
                        "1. Shenhe Skill (E) -> Burst (Q) for Cryo RES shred and Icy Quills.",
                        "2. Kazuha Skill/Burst to gather enemies and buff Cryo DMG.",
                        "3. Kokomi Jellyfish (E) to apply continuous AoE Hydro.",
                        "4. Ayaka Dash -> Burst (Q) for massive concentrated blizzard slash."
                    ],
                    "variants": ["Ganyu Morgana", "Wriothesley Freeze", "Kaeya/Rosaria F2P Freeze"]
                }
            ]
        return self._teams_cache

    def _get_all_mechanics(self) -> List[Dict[str, Any]]:
        """Return structured game mechanics guides."""
        if self._mechanics_cache is None:
            self._mechanics_cache = [
                {
                    "id": "mech_elemental_reactions",
                    "slug": "elemental_reactions",
                    "title": "Elemental Reactions & Multipliers",
                    "topic": "Combat Mathematics",
                    "summary": "Complete breakdown of Amplifying (Vaporize, Melt), Catalyze (Aggravate, Spread), and Transformative (Swirl, Hyperbloom, Electro-Charged, Overload) reaction math.",
                    "visual_sections": [
                        {"title": "Amplifying Reactions", "desc": "Multiplies attack damage: Forward Vape (2.0x), Reverse Vape (1.5x), Forward Melt (2.0x), Reverse Melt (1.5x). Can critically strike."},
                        {"title": "Catalyze Reactions", "desc": "Quicken aura enables Aggravate (Electro bonus) and Spread (Dendro bonus), adding flat base damage scaling with EM and character level."},
                        {"title": "Transformative Reactions", "desc": "Separate damage instances determined solely by triggering character level, Elemental Mastery, and enemy RES (cannot crit without special passives)."}
                    ],
                    "key_formulas": [
                        "Vaporize (Hydro on Pyro): DMG = AttackDMG × 2.0 × (1 + EM_Bonus + Special_Bonus)",
                        "Transformative DMG = BaseReaction(Level) × ReactionMultiplier × (1 + EM_Bonus) × EnemyResMult"
                    ],
                    "takeaways": [
                        "Forward reactions consume twice as much elemental aura as reverse reactions.",
                        "Transformative reactions completely ignore character ATK and talent level scalings."
                    ]
                },
                {
                    "id": "mech_damage_formula",
                    "slug": "damage_formula",
                    "title": "Incoming & Outgoing Damage Formula",
                    "topic": "Theorycrafting Core",
                    "summary": "The master equation that dictates every damage number in Genshin Impact, from base scaling to defense and resistance calculations.",
                    "visual_sections": [
                        {"title": "Base Damage", "desc": "(Base ATK × ATK% + Flat ATK) × Talent% + Flat Buffs (Shenhe, Yun Jin, Bennett)."},
                        {"title": "Damage Bonus Multiplier", "desc": "1 + Elemental DMG% + Skill/Burst DMG% + Normal/Charged DMG% + All DMG%."},
                        {"title": "CRIT Multiplier", "desc": "On non-crit: 1.0. On crit: 1 + CRIT DMG%."},
                        {"title": "Enemy Defense & Resistance", "desc": "DefMult = (CharLevel + 100) / ((CharLevel + 100) + (EnemyLevel + 100) × (1 - DefShred))."}
                    ],
                    "key_formulas": [
                        "Final DMG = BaseDamage × DMG_Bonus × CRIT × Reaction × DefenseMult × ResistanceMult"
                    ],
                    "takeaways": [
                        "Balancing ATK%, DMG%, and CRIT yields far higher returns than over-investing in a single stat due to multiplicative product scaling.",
                        "RES shred below 0% is halved in effectiveness (e.g. -40% VV becomes -20% against 0% RES target)."
                    ]
                },
                {
                    "id": "mech_energy_recharge",
                    "slug": "energy_recharge",
                    "title": "Energy Recharge, Funneling & Particles",
                    "topic": "Rotations & Combat",
                    "summary": "How elemental particles generate burst energy, off-field reduction penalties, Favonius neutral particles, and battery funneling techniques.",
                    "visual_sections": [
                        {"title": "Elemental Particles", "desc": "Matching element particle grants 3 energy on-field and 1.8 energy off-field. Non-matching grants 1 on-field and 0.6 off-field."},
                        {"title": "Clear / Neutral Particles", "desc": "Favonius weapons generate clear particles granting 2 energy on-field and 1.2 energy off-field to all party members."},
                        {"title": "Funneling Technique", "desc": "Triggering a skill on a battery (e.g. Bennett E) and immediately swapping to a hungry carry (Xiangling) catches particles on-field for 300% energy gain."}
                    ],
                    "key_formulas": [
                        "Energy Gained = BaseParticleValue × ParticleCount × ER_Multiplier"
                    ],
                    "takeaways": [
                        "Catching matching particles on-field provides 3x more energy than catching non-matching particles off-field.",
                        "Favonius weapons eliminate particle mismatch penalties and smoothen team burst rotations."
                    ]
                },
                {
                    "id": "mech_snapshotting",
                    "slug": "snapshotting",
                    "title": "Snapshotting & Dynamic Buffs",
                    "topic": "Combat Mechanics",
                    "summary": "Explains which deployable skills snapshot character stats upon cast vs which update dynamically in real time.",
                    "visual_sections": [
                        {"title": "Snapshotting Abilities", "desc": "Xiangling Pyronado, Beidou Stormcaller, Ganyu Celestial Shower lock in ATK and buffs (Bennett, Noblesse) for the entire duration."},
                        {"title": "Dynamic Abilities", "desc": "Xingqiu Raincutters, Yelan Exquisite Throw, Furina Salon Solitaire calculate stats dynamically on every hit; leaving buffs loses bonus immediately."}
                    ],
                    "key_formulas": [
                        "Snapshotted DMG = StatsAtCastTime × Multipliers (persists even if buff expires)"
                    ],
                    "takeaways": [
                        "Always cast snapshot abilities while standing inside Bennett's field or while buffs are active.",
                        "Transformative reactions (Hyperbloom, Swirl) are strictly dynamic and never snapshot character EM or level."
                    ]
                }
            ]
        return self._mechanics_cache


guide_service = GuideService()
