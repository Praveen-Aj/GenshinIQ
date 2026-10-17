"""Encyclopedia Service for GenshinIQ.

Provides structured, high-density character build guides, dynamic stat scaling,
weapon refinement progressions, and team synergies for the Phase 11 encyclopedia UI.
"""

from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional, Tuple
from backend.services.stat_engine import stat_engine_service
from backend.services.game_data_service import game_data_service


def get_default_ascension_for_level(level: int) -> int:
    """Return canonical max ascension tier for given level 1-90."""
    if level <= 20:
        return 0
    if level <= 40:
        return 1
    if level <= 50:
        return 2
    if level <= 60:
        return 3
    if level <= 70:
        return 4
    if level <= 80:
        return 5
    return 6


class EncyclopediaService:
    """Service providing rich encyclopedia views, build guides, and scaling math."""

    def __init__(self):
        self.root_dir = Path(__file__).resolve().parent.parent.parent
        self.knowledge_dir = self.root_dir / "data" / "knowledge"
        self.processed_dir = self.root_dir / "data" / "processed" / "game_data"
        self._guide_cache: Dict[str, Dict[str, Any]] = {}
        self._teams_registry: Dict[str, List[Dict[str, Any]]] = self._init_teams_registry()
        self._farming_schedule = self._load_farming_schedule()

    def _load_farming_schedule(self) -> Dict[str, Any]:
        """Load talent books schedule."""
        sched_file = self.knowledge_dir / "structured_daily_talent_books_schedule.json"
        if sched_file.exists():
            try:
                with open(sched_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _init_teams_registry(self) -> Dict[str, List[Dict[str, Any]]]:
        """Authoritative team archetype definitions for notable characters."""
        return {
            "kaedehara kazuha": [
                {
                    "name": "International",
                    "archetype": "Vaporize",
                    "members": ["Tartaglia", "Xiangling", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Tartaglia E -> Bennett Q -> Kazuha Q E -> Xiangling Q E -> Tartaglia Melee",
                },
                {
                    "name": "Raiden Hypercarry",
                    "archetype": "Hypercarry",
                    "members": ["Raiden Shogun", "Kujou Sara", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Raiden E -> Kazuha Q E -> Bennett Q -> Sara Q -> Raiden Q",
                },
                {
                    "name": "Ayaka Premium Freeze",
                    "archetype": "Freeze",
                    "members": ["Kamisato Ayaka", "Shenhe", "Kaedehara Kazuha", "Sangonomiya Kokomi"],
                    "rotation": "Shenhe E Q -> Kazuha E Q -> Kokomi E -> Ayaka Dash Q E",
                },
            ],
            "furina": [
                {
                    "name": "Neuvillette Hypercarry",
                    "archetype": "Hypercarry",
                    "members": ["Neuvillette", "Furina", "Kaedehara Kazuha", "Baizhu"],
                    "rotation": "Furina E Q -> Neuvillette E -> Kazuha E Q -> Baizhu E Q -> Neuvillette CA",
                },
                {
                    "name": "Furina National",
                    "archetype": "Vaporize",
                    "members": ["Furina", "Xiangling", "Bennett", "Jean"],
                    "rotation": "Furina E Q -> Bennett E Q -> Jean Q -> Xiangling Q E -> Furina/Jean Driver",
                },
                {
                    "name": "Xiao Plunge Hyper",
                    "archetype": "Plunge / Hyper",
                    "members": ["Xiao", "Xianyun", "Faruzan", "Furina"],
                    "rotation": "Furina E Q -> Faruzan Q -> Xianyun E Q -> Xiao EE Q Plunge",
                },
            ],
            "arlecchino": [
                {
                    "name": "Arlecchino Vaporize",
                    "archetype": "Vaporize",
                    "members": ["Arlecchino", "Yelan", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Arlecchino E -> Zhongli/Kazuha E -> Yelan Q E -> Bennett Q -> Arlecchino CA Normal Combos",
                },
                {
                    "name": "Chevreuse Overload",
                    "archetype": "Overload",
                    "members": ["Arlecchino", "Chevreuse", "Fischl", "Bennett"],
                    "rotation": "Fischl E -> Chevreuse Hold E Q -> Bennett Q -> Arlecchino CA Normal Combos",
                },
                {
                    "name": "Zhongli Mono-Pyro",
                    "archetype": "Mono-Pyro",
                    "members": ["Arlecchino", "Xiangling", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Arlecchino E -> Kazuha E Q -> Bennett Q -> Xiangling Q E -> Arlecchino CA Normal Combos",
                },
            ],
            "raiden shogun": [
                {
                    "name": "Raiden National (Rational)",
                    "archetype": "Overvape",
                    "members": ["Raiden Shogun", "Xiangling", "Xingqiu", "Bennett"],
                    "rotation": "Raiden E -> Xingqiu Q EE -> Bennett Q E -> Xiangling Q E -> Raiden Q Attacks",
                },
                {
                    "name": "Raiden Hypercarry",
                    "archetype": "Hypercarry",
                    "members": ["Raiden Shogun", "Kujou Sara", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Raiden E -> Kazuha Q E -> Bennett Q -> Sara Q -> Raiden Q Attacks",
                },
                {
                    "name": "Alhaitham Quickbloom",
                    "archetype": "Quickbloom",
                    "members": ["Alhaitham", "Nahida", "Xingqiu", "Raiden Shogun"],
                    "rotation": "Raiden E -> Nahida E Q -> Xingqiu Q EE -> Alhaitham Hold E Plunge Combos",
                },
            ],
            "neuvillette": [
                {
                    "name": "Neuvillette Premium Hyper",
                    "archetype": "Hypercarry",
                    "members": ["Neuvillette", "Furina", "Kaedehara Kazuha", "Baizhu"],
                    "rotation": "Furina E Q -> Neuvillette E -> Kazuha E Q -> Baizhu E Q -> Neuvillette CA",
                },
                {
                    "name": "Neuvillette Rainbow Hyper",
                    "archetype": "Draconic Stacks",
                    "members": ["Neuvillette", "Fischl", "Kaedehara Kazuha", "Zhongli"],
                    "rotation": "Zhongli Hold E -> Neuvillette E -> Kazuha E -> Fischl E -> Neuvillette CA Q CA",
                },
            ],
            "nahida": [
                {
                    "name": "Alhaitham Spread",
                    "archetype": "Spread",
                    "members": ["Alhaitham", "Nahida", "Yae Miko", "Zhongli"],
                    "rotation": "Zhongli Hold E -> Nahida E Q -> Yae EEE -> Alhaitham Hold E Plunge Combos",
                },
                {
                    "name": "Nilou Superbloom",
                    "archetype": "Bountiful Bloom",
                    "members": ["Nilou", "Nahida", "Sangonomiya Kokomi", "Collei"],
                    "rotation": "Nahida E Q -> Nilou EEEE -> Kokomi E -> Collei E Q -> Kokomi Normal Attacks",
                },
            ],
            "hu tao": [
                {
                    "name": "Double Hydro Hu Tao",
                    "archetype": "Vaporize",
                    "members": ["Hu Tao", "Xingqiu", "Yelan", "Zhongli"],
                    "rotation": "Zhongli Hold E -> Xingqiu Q EE -> Yelan Q EE -> Hu Tao E N2CD Combos",
                },
                {
                    "name": "VV Vape Hu Tao",
                    "archetype": "Vaporize",
                    "members": ["Hu Tao", "Xingqiu", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Xingqiu Q EE -> Bennett Q E -> Kazuha E Q -> Hu Tao E Charged Attacks",
                },
            ],
            "bennett": [
                {
                    "name": "National Classic",
                    "archetype": "Vaporize",
                    "members": ["Xiangling", "Xingqiu", "Bennett", "Sucrose"],
                    "rotation": "Xingqiu Q EE -> Bennett Q E -> Sucrose E -> Xiangling Q E",
                },
                {
                    "name": "Sunfire Jean",
                    "archetype": "Swirl / Vape",
                    "members": ["Raiden Shogun", "Jean", "Bennett", "Xingqiu"],
                    "rotation": "Raiden E -> Xingqiu Q EE -> Bennett Q -> Jean Q -> Raiden Q",
                },
            ],
            "xiangling": [
                {
                    "name": "International",
                    "archetype": "Vaporize",
                    "members": ["Tartaglia", "Xiangling", "Kaedehara Kazuha", "Bennett"],
                    "rotation": "Childe E -> Bennett Q -> Kazuha Q E -> Xiangling Q E -> Childe Melee",
                },
                {
                    "name": "Rational",
                    "archetype": "Overvape",
                    "members": ["Raiden Shogun", "Xiangling", "Xingqiu", "Bennett"],
                    "rotation": "Raiden E -> Xingqiu Q EE -> Bennett Q E -> Xiangling Q E -> Raiden Q",
                },
            ],
            "zhongli": [
                {
                    "name": "Universal Comfort Shield",
                    "archetype": "Universal Support",
                    "members": ["Hu Tao", "Xingqiu", "Yelan", "Zhongli"],
                    "rotation": "Zhongli Hold E (20s 20% all-RES shred + unbreakable shield) -> Carry rotation",
                }
            ],
            "mavuika": [
                {
                    "name": "Nightsoul Burst Vaporize",
                    "archetype": "Nightsoul / Vape",
                    "members": ["Mavuika", "Citlali", "Furina", "Xilonen"],
                    "rotation": "Xilonen E Q -> Furina E Q -> Citlali E Q -> Mavuika E Q Drive",
                }
            ],
        }

    def get_character_scaling(
        self,
        character_name_or_id: str,
        level: int = 90,
        ascension: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Compute exact canonical base stats and ascension bonuses for any character at any level 1-90."""
        if ascension is None:
            ascension = get_default_ascension_for_level(level)

        base, asc, status, warnings = stat_engine_service.resolve_character_base_stats(
            character_name_or_id,
            level=level,
            ascension=ascension,
        )
        canonical = game_data_service.get_character(character_name_or_id)
        c_name = canonical.name if canonical else str(character_name_or_id)

        return {
            "name": c_name,
            "level": level,
            "ascension": ascension,
            "base_hp": base.get("hp", 0.0),
            "base_atk": base.get("atk", 0.0),
            "base_def": base.get("def_", 0.0),
            "ascension_stats": asc,
            "status": status.value if hasattr(status, "value") else str(status),
            "warnings": warnings,
        }

    def get_weapon_scaling(
        self,
        weapon_name_or_id: str,
        level: int = 90,
        ascension: Optional[int] = None,
        refinement: int = 1,
    ) -> Dict[str, Any]:
        """Compute exact canonical weapon stats and refinement bonuses at any level 1-90 and R1-R5."""
        if ascension is None:
            ascension = get_default_ascension_for_level(level)

        base_atk, sub_name, sub_val, static_passives, status, warnings = (
            stat_engine_service.resolve_weapon_stats(
                weapon_name_or_id,
                level=level,
                ascension=ascension,
                refinement=refinement,
            )
        )
        canonical = game_data_service.get_weapon(weapon_name_or_id)
        w_name = canonical.name if canonical else str(weapon_name_or_id)

        sub_formatted = ""
        if sub_name and sub_val > 0:
            if any(term in sub_name for term in ["%", "Bonus", "Rate", "DMG", "Recharge"]):
                sub_formatted = f"{(sub_val * 100):.1f}%"
            else:
                sub_formatted = str(int(round(sub_val)))

        return {
            "name": w_name,
            "level": level,
            "ascension": ascension,
            "refinement": refinement,
            "base_atk": base_atk,
            "sub_stat_type": sub_name,
            "sub_stat_val": sub_val,
            "sub_stat_formatted": sub_formatted,
            "static_passives": static_passives,
            "status": status.value if hasattr(status, "value") else str(status),
            "warnings": warnings,
        }

    def get_character_build_guide(self, character_name_or_id: str) -> Dict[str, Any]:
        """Compile a 10-section ready build guide for the specified character."""
        canonical = game_data_service.get_character(character_name_or_id)
        if not canonical:
            return {}

        c_name = canonical.name
        c_key = c_name.lower()
        if c_key in self._guide_cache:
            return self._guide_cache[c_key]

        # 1. Inspect KQM document if available
        kqm_file = self.knowledge_dir / f"kqm_{c_key.replace(' ', '_')}_guide.json"
        if not kqm_file.exists():
            for f in self.knowledge_dir.glob("kqm_*_guide.json"):
                if c_key.replace(" ", "") in f.name.replace("_", ""):
                    kqm_file = f
                    break

        kqm_content = ""
        if kqm_file.exists():
            try:
                with open(kqm_file, "r", encoding="utf-8") as f:
                    kqm_data = json.load(f)
                    kqm_content = kqm_data.get("content", "")
            except Exception:
                pass

        # Authoritative list of characters with curated KQM theorycrafting guides
        curated_characters = {
            "kaedehara kazuha", "furina", "arlecchino", "alhaitham", "bennett",
            "citlali", "hu tao", "mavuika", "nahida", "neuvillette",
            "raiden shogun", "xiangling", "xingqiu", "yelan", "zhongli"
        }
        is_curated = c_key in curated_characters or (kqm_file.exists() and len(kqm_content) > 100)

        guide_type = "CURATED_CHARACTER_GUIDE" if is_curated else "GENERIC_FALLBACK"
        guide_provenance = "KeqingMains Curated Theorycrafting" if is_curated else "Elemental / Weapon Baseline Archetype"

        # 2. Extract sections from KQM or construct canonical defaults
        summary_role = self._extract_role(c_name, kqm_content, canonical)
        strengths = self._extract_strengths(c_name, kqm_content, canonical)
        caveats = self._extract_caveats(c_name, kqm_content, canonical)
        talent_prio = self._extract_talent_priority(c_name, kqm_content, canonical)
        weapons = self._extract_weapons(c_name, kqm_content, canonical)
        artifacts = self._extract_artifacts(c_name, kqm_content, canonical)
        main_stats, substats, benchmarks = self._extract_stats(c_name, kqm_content, canonical)
        teams = self._teams_registry.get(c_key, self._generate_fallback_teams(canonical))
        farming = self._compile_farming_info(canonical)

        guide = {
            "character_id": str(canonical.id),
            "character_name": c_name,
            "guide_type": guide_type,
            "guide_provenance": guide_provenance,
            "role": summary_role,
            "strengths": strengths,
            "caveats": caveats,
            "talent_priority": talent_prio,
            "recommended_weapons": weapons,
            "recommended_artifacts": artifacts,
            "main_stats": main_stats,
            "substat_priorities": substats,
            "stat_benchmarks": benchmarks,
            "teams": teams,
            "farming": farming,
        }

        self._guide_cache[c_key] = guide
        return guide

    def _extract_role(self, name: str, content: str, char: Any) -> str:
        """Derive scannable role string."""
        if "Sub-DPS and universal damage buffer" in content:
            return "Off-Field Sub-DPS & Universal DMG Buffer"
        if "premier elemental buffers and crowd-controllers" in content:
            return "Crowd Control & Elemental DMG Buffer"
        if "Nightsoul" in content:
            return "Nightsoul Driver & Main DPS"
        if char.weapon_type == "Bow" and char.element == "Hydro":
            return "Off-Field Hydro Sub-DPS"
        if char.element == "Anemo":
            return "Anemo Support & Resistance Shredder"
        if char.rarity == 5:
            return f"{char.element} Carry / Specialist"
        return f"{char.element} Support / Sub-DPS"

    def _extract_strengths(self, name: str, content: str, char: Any) -> List[str]:
        """Extract or generate visual strength tags."""
        if "Furina" in name:
            return ["Universal Team DMG Buff", "Dynamic HP Consumption", "Consistent Off-field Hydro", "Water Walking"]
        if "Kazuha" in name:
            return ["Massive EM-scaling DMG Buff", "Top-tier Grouping & Pull", "Double Swirl VV Shred", "Midare Ranzan Plunge"]
        if "Arlecchino" in name:
            return ["Bond of Life Infusion", "Explosive Normal Attack Combos", "Independent Self-Sustaining", "High Pyro DPS"]
        if "Raiden" in name:
            return ["Universal Energy Battery", "Burst DMG Amplification", "High Hypercarry Scaling", "Coordinated Electro Hits"]
        if "Bennett" in name:
            return ["Massive Flat ATK Buff", "Rapid Burst Healing", "Pyro Resonance & Battery", "Universal Compatibility"]
        if "Xiangling" in name:
            return ["No ICD Pyronado", "Stat Snapshotting", "Off-field Vaporize Kingpin", "High AoE Pyro"]
        if "Zhongli" in name:
            return ["Impervious Jade Shield", "20% Universal RES Shred", "Petrification CC", "Zero Interruption"]
        return [f"Strong {char.element} Synergy", f"Effective {char.weapon_type} Scaling", "Consistent Rotation"]

    def _extract_caveats(self, name: str, content: str, char: Any) -> List[str]:
        """Extract visual caveat tags."""
        if "Furina" in name:
            return ["Party HP Drain requires healer", "High ER requirement in Solo Hydro (180%+)"]
        if "Kazuha" in name:
            return ["Requires strict double-swirl rotation", "Strict ER needs if using non-Favonius weapon"]
        if "Arlecchino" in name:
            return ["Cannot be healed by party in combat", "Vulnerable to staggering without shield/dodge"]
        if "Xiangling" in name:
            return ["Severe 80 Energy Burst Cost", "Tethered to Bennett battery for optimal uptime"]
        if "Hu Tao" in name:
            return ["Requires stamina management at C0", "Prefers maintaining HP < 50% for passive"]
        return ["Demands appropriate ER for burst uptime", "Elemental aura balance in reaction teams"]

    def _extract_talent_priority(self, name: str, content: str, char: Any) -> str:
        """Extract talent priority string."""
        if "Furina" in name:
            return "Skill (Lv. 10) = Burst (Lv. 10) >> Normal Attack (Lv. 1)"
        if "Kazuha" in name:
            return "Burst (Lv. 8+) >= Skill (Lv. 8+) > Normal Attack (Lv. 8+)"
        if "Arlecchino" in name:
            return "Normal Attack (Lv. 10) >> Skill (Lv. 8+) > Burst (Lv. 8)"
        if "Raiden" in name:
            return "Burst (Lv. 10) >> Skill (Lv. 9) > Normal Attack (Lv. 1)"
        if "Bennett" in name:
            return "Burst (Crown Lv. 10) >> Skill (Lv. 8) > Normal Attack (Lv. 1)"
        if "Xiangling" in name:
            return "Burst (Crown Lv. 10) >> Skill (Lv. 8+) > Normal Attack (Lv. 1)"
        if "Neuvillette" in name:
            return "Normal/Charged (Crown Lv. 10) >> Burst (Lv. 8) = Skill (Lv. 8)"
        return "Burst > Skill >> Normal Attack"

    def _extract_weapons(self, name: str, content: str, char: Any) -> List[Dict[str, Any]]:
        """Extract top weapon recommendations."""
        if "Furina" in name:
            return [
                {"name": "Splendor of Tranquil Waters", "rarity": 5, "badge": "BiS / Signature", "desc": "Highest personal damage, CRIT DMG & HP buffs."},
                {"name": "Key of Khaj-Nisut", "rarity": 5, "badge": "BiS Alternative", "desc": "Massive HP% and party-wide EM buffs in reaction teams."},
                {"name": "Fleuve Cendre Ferryman", "rarity": 4, "badge": "Top F2P (R5)", "desc": "Fishing sword with high ER and +16% Skill CRIT Rate."},
                {"name": "Favonius Sword", "rarity": 4, "badge": "Team Energy", "desc": "Neutral energy particles, lowers team-wide ER requirements."},
            ]
        if "Kazuha" in name:
            return [
                {"name": "Freedom-Sworn", "rarity": 5, "badge": "BiS / Signature", "desc": "Top team utility; grants EM and team ATK% + Normal DMG."},
                {"name": "Xiphos' Moonlight", "rarity": 4, "badge": "Top 4★ (R5)", "desc": "Converts EM into personal and party ER."},
                {"name": "Favonius Sword", "rarity": 4, "badge": "Top Utility", "desc": "Guarantees reliable 100% Burst uptime."},
                {"name": "Iron Sting", "rarity": 4, "badge": "F2P Craftable", "desc": "Pure EM stat stick for maximum Swirl buffs."},
            ]
        if "Arlecchino" in name:
            return [
                {"name": "Crimson Moon's Semblance", "rarity": 5, "badge": "BiS / Signature", "desc": "Signature polearm providing Bond of Life on CA."},
                {"name": "Staff of Homa", "rarity": 5, "badge": "Alternative 5★", "desc": "High CRIT DMG and bonus ATK based on Max HP."},
                {"name": "Deathmatch", "rarity": 4, "badge": "Battle Pass", "desc": "High CRIT Rate and consistent ATK/DEF buffs."},
                {"name": "White Tassel", "rarity": 3, "badge": "Best F2P (R5)", "desc": "Chest weapon granting massive +48% Normal Attack DMG."},
            ]
        type_defaults = {
            "Sword": [
                {"name": "Mistsplitter Reforged", "rarity": 5, "badge": "Top 5★", "desc": "High base ATK, CRIT DMG, and elemental damage stacks."},
                {"name": "Favonius Sword", "rarity": 4, "badge": "Energy BiS", "desc": "Universal energy battery for comfortable rotations."},
            ],
            "Claymore": [
                {"name": "Serpent Spine", "rarity": 4, "badge": "Top 4★", "desc": "High CRIT Rate and ramping DMG bonus."},
                {"name": "Favonius Greatsword", "rarity": 4, "badge": "Energy BiS", "desc": "High ER and team particle generation."},
            ],
            "Polearm": [
                {"name": "Staff of Homa", "rarity": 5, "badge": "Top 5★", "desc": "Premier CRIT DMG polearm."},
                {"name": "The Catch", "rarity": 4, "badge": "F2P BiS (R5)", "desc": "Free fishing weapon with Burst DMG & CRIT Rate."},
            ],
            "Bow": [
                {"name": "Aqua Simulacra", "rarity": 5, "badge": "Top 5★", "desc": "Massive 88.2% CRIT DMG and universal 20% DMG buff."},
                {"name": "Favonius Warbow", "rarity": 4, "badge": "Support BiS", "desc": "Reliable particle generation for bow supports."},
            ],
            "Catalyst": [
                {"name": "Tome of the Eternal Flow", "rarity": 5, "badge": "Top 5★", "desc": "Signature HP scaling catalyst with CRIT DMG."},
                {"name": "Widsith", "rarity": 4, "badge": "Top 4★ (R5)", "desc": "High burst CRIT DMG and powerful random song buffs."},
            ],
        }
        return type_defaults.get(char.weapon_type, [])

    def _extract_artifacts(self, name: str, content: str, char: Any) -> List[Dict[str, Any]]:
        """Extract top artifact sets with canonical set_name, pieces, badge, and notes."""
        if "Furina" in name:
            raw_sets = [
                {"set_name": "Golden Troupe", "pieces": 4, "badge": "BiS (Non-Negotiable)", "notes": "+70% Elemental Skill DMG when off-field."},
                {"set_name": "2pc HP% + 2pc Golden Troupe", "pieces": 2, "badge": "Transitional", "notes": "Viable balanced combination while farming 4pc."},
            ]
        elif "Kazuha" in name:
            raw_sets = [
                {"set_name": "Viridescent Venerer", "pieces": 4, "badge": "BiS (Mandatory)", "notes": "Shreds swirled elemental resistance by 40% for 10s."},
                {"set_name": "2pc EM + 2pc EM", "pieces": 2, "badge": "Early Game", "notes": "+160 flat EM while securing 4pc VV."},
            ]
        elif "Arlecchino" in name:
            raw_sets = [
                {"set_name": "Fragment of Harmonic Whimsy", "pieces": 4, "badge": "BiS / Signature", "notes": "+54% DMG increase via Bond of Life fluctuations."},
                {"set_name": "Gladiator's Finale", "pieces": 4, "badge": "Top Accessible", "notes": "+35% Normal Attack DMG with zero setup."},
            ]
        elif "Raiden" in name or "Xiangling" in name or "Xingqiu" in name or "Yelan" in name:
            raw_sets = [
                {"set_name": "Emblem of Severed Fate", "pieces": 4, "badge": "BiS (Standard)", "notes": "Converts Energy Recharge directly into up to 75% Burst DMG."},
            ]
        else:
            raw_sets = [
                {"set_name": "Noblesse Oblige", "pieces": 4, "badge": "Support Standard", "notes": "+20% Burst DMG and +20% party ATK buff."},
                {"set_name": "2pc +18% ATK / 2pc Elemental DMG", "pieces": 2, "badge": "General", "notes": "Stat-efficient general setup."},
            ]

        # Ensure both set_name/name and notes/desc are populated for full contract agreement
        normalized = []
        for s in raw_sets:
            s_name = s.get("set_name") or s.get("name", "")
            s_notes = s.get("notes") or s.get("desc", "")
            normalized.append({
                "set_name": s_name,
                "name": s_name,
                "pieces": s.get("pieces", 4),
                "badge": s.get("badge", "Recommended"),
                "notes": s_notes,
                "desc": s_notes,
            })
        return normalized

    def _extract_stats(self, name: str, content: str, char: Any) -> Tuple[Dict[str, str], List[str], Dict[str, str]]:
        """Extract main stats, substat priority, and benchmarks."""
        if "Furina" in name:
            return (
                {"sands": "HP% or Energy Recharge", "goblet": "HP% or Hydro DMG%", "circlet": "CRIT Rate or CRIT DMG"},
                ["Energy Recharge (to threshold)", "CRIT Rate / CRIT DMG", "HP%", "Elemental Mastery"],
                {"er": "160-180% (Double Hydro) / 200%+ (Solo)", "crit_ratio": "70% / 140%+", "hp": "36,000 - 40,000"},
            )
        if "Kazuha" in name:
            return (
                {"sands": "Elemental Mastery (or ER%)", "goblet": "Elemental Mastery", "circlet": "Elemental Mastery"},
                ["Elemental Mastery", "Energy Recharge (160%+)", "CRIT Rate (if using Favonius)", "ATK%"],
                {"em": "900 - 1000+", "er": "160% (Favonius) / 180%+ (Iron Sting)", "crit_rate": "30%+ (Favonius trigger)"},
            )
        if "Arlecchino" in name:
            return (
                {"sands": "ATK% (or EM in Vape)", "goblet": "Pyro DMG Bonus", "circlet": "CRIT Rate or CRIT DMG"},
                ["CRIT Rate / CRIT DMG", "ATK%", "Elemental Mastery (Vape)", "Energy Recharge"],
                {"crit_ratio": "75% / 160%+", "atk": "2,200+", "em": "100 - 150 (in Vape)"},
            )
        return (
            {"sands": "ATK% / ER% / HP%", "goblet": f"{char.element} DMG Bonus", "circlet": "CRIT Rate / CRIT DMG"},
            ["CRIT Rate / CRIT DMG", "Energy Recharge", "ATK% / HP%", "Elemental Mastery"],
            {"crit_ratio": "60% / 120%+", "er": "140% - 160%"},
        )

    def _compile_farming_info(self, char: Any) -> Dict[str, Any]:
        """Compile farming materials with nation talent schedule, resolving any raw numeric IDs."""
        region_domains = {
            "MONDSTADT": "Forsaken Rift (Mondstadt)",
            "LIYUE": "Taishan Mansion (Liyue)",
            "INAZUMA": "Violet Court (Inazuma)",
            "SUMERU": "Steeple of Ignorance (Sumeru)",
            "FONTAINE": "Pale Forgotten Glory (Fontaine)",
            "NATLAN": "Blazing Ruins (Natlan)",
        }
        reg = (char.region or "Mondstadt").upper()
        domain_name = region_domains.get(reg, "Regional Mastery Domain")

        # Resolve ascension materials (never allow raw numeric ID in consumer payload)
        resolved_asc_mats = []
        for mat in (char.ascension_materials or []):
            mat_str = str(mat).strip()
            if mat_str.isdigit():
                m_obj = game_data_service.get_material(mat_str)
                resolved_asc_mats.append(m_obj.name if m_obj else f"Material {mat_str}")
            else:
                resolved_asc_mats.append(mat_str)

        # Resolve talent materials
        resolved_talent_mats = []
        for mat in (char.talent_materials or []):
            mat_str = str(mat).strip()
            if mat_str.isdigit():
                m_obj = game_data_service.get_material(mat_str)
                resolved_talent_mats.append(m_obj.name if m_obj else f"Material {mat_str}")
            else:
                resolved_talent_mats.append(mat_str)

        return {
            "region": char.region or "Teyvat",
            "domain_location": domain_name,
            "talent_materials": resolved_talent_mats,
            "ascension_materials": resolved_asc_mats,
            "daily_availability": "Check today's rotation planner on My Account tab",
        }

    def _generate_fallback_teams(self, char: Any) -> List[Dict[str, Any]]:
        """Generate sensible team comp fallback based on element."""
        elem = char.element
        if elem == "Cryo":
            return [
                {"name": f"{char.name} Freeze", "archetype": "Freeze", "members": [char.name, "Kaedehara Kazuha", "Furina", "Charlotte"], "rotation": "Apply Hydro -> Kazuha Swirl -> Freeze -> Cryo DPS"},
                {"name": f"{char.name} Melt", "archetype": "Melt", "members": [char.name, "Xiangling", "Bennett", "Zhongli"], "rotation": "Zhongli Shield -> Bennett Q -> Xiangling Q -> Cryo Melt"},
            ]
        if elem == "Pyro":
            return [
                {"name": f"{char.name} Vaporize", "archetype": "Vaporize", "members": [char.name, "Yelan", "Xingqiu", "Zhongli"], "rotation": "Zhongli Shield -> Xingqiu Q -> Yelan Q -> Pyro DPS"},
                {"name": f"{char.name} Overload", "archetype": "Overload", "members": [char.name, "Chevreuse", "Fischl", "Bennett"], "rotation": "Chevreuse E -> Fischl E -> Bennett Q -> Pyro DPS"},
            ]
        if elem == "Hydro":
            return [
                {"name": f"{char.name} Electro-Charged", "archetype": "Taser", "members": [char.name, "Fischl", "Beidou", "Kaedehara Kazuha"], "rotation": "Hydro Apply -> Electro -> Kazuha Swirl -> Drive"},
            ]
        if elem == "Dendro":
            return [
                {"name": f"{char.name} Hyperbloom", "archetype": "Hyperbloom", "members": [char.name, "Nahida", "Xingqiu", "Kuki Shinobu"], "rotation": "Nahida E -> Xingqiu Q -> Shinobu E -> Dendro Driver"},
            ]
        if elem == "Electro":
            return [
                {"name": f"{char.name} Aggravate", "archetype": "Aggravate", "members": [char.name, "Nahida", "Kaedehara Kazuha", "Kuki Shinobu"], "rotation": "Electro -> Kazuha Swirl -> Nahida E -> Electro Carry"},
            ]
        if elem == "Geo":
            return [
                {"name": f"{char.name} Mono-Geo", "archetype": "Mono-Geo", "members": [char.name, "Gorou", "Albedo", "Zhongli"], "rotation": "Zhongli Shield -> Gorou E Q -> Albedo E -> Geo Burst"},
            ]
        return [
            {"name": f"{char.name} Core Synergy", "archetype": "Universal", "members": [char.name, "Kaedehara Kazuha", "Bennett", "Zhongli"], "rotation": "Buff -> Debuff -> Damage Window"},
        ]


encyclopedia_service = EncyclopediaService()
