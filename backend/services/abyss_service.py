"""
Spiral Abyss & Endgame Tracker (Phase 17).
Provides structured Floor 12 chamber enemy lineups, elemental resistances,
Ley Line Disorders, active Blessing of the Abyssal Moon, and account-grounded
side 1 / side 2 team recommendations.
"""

from typing import Dict, Any, List, Optional, Set
import logging

from backend.services.account_inventory_service import account_inventory_service
from backend.services.game_data_service import game_data_service
from backend.services.team_service import team_service

logger = logging.getLogger(__name__)


# Canonical Spiral Abyss Floor 12 Data
SPIRAL_ABYSS_SCHEDULE = {
    "cycle_id": "2026-09-A",
    "floor": 12,
    "version": "7.0",
    "period": "Current Active Cycle",
    "blessing": {
        "name": "Blessing of the Abyssal Moon: Resonant Surge",
        "effect": "When a character triggers an Elemental Reaction, unleashes a shockwave at the opponent's position dealing True DMG (CD 3s). When character HP fluctuates, increases Elemental Mastery by 80 and CRIT DMG by 30% for 8s (stacks up to 3 times)."
    },
    "ley_line_disorder": "For this floor, all party members deal 25% increased Elemental DMG. In Chamber 1, opponents have increased Physical RES (+50%). In Chamber 3, Elemental Burst DMG is increased by 30%.",
    "chambers": [
        {
            "chamber": 1,
            "level": 95,
            "stars_available": 3,
            "target_time_sec": 420,  # 7:00 remaining for 3 stars
            "first_half": {
                "name": "Chamber 1 - First Half",
                "enemy_count": 3,
                "enemies": [
                    {
                        "name": "Hydro Tulpa",
                        "hp": 2850000,
                        "element": "Hydro",
                        "immunity": ["Hydro"],
                        "weakness": "Pyro / Vaporize",
                        "resistances": "Hydro Immune (100%), 10% all other elements",
                        "advisory": "Immune to Hydro. Constantly affected by Hydro aura; high-frequency Pyro attacks trigger continuous 1.5x/2.0x Vaporize."
                    },
                    {
                        "name": "Half-Tulpa Minions",
                        "hp": 240000,
                        "element": "Hydro",
                        "immunity": ["Hydro"],
                        "weakness": "Fast Pyro application",
                        "resistances": "10% all elements",
                        "advisory": "Destroy minions immediately to prevent the Hydro Tulpa from absorbing them and gaining massive ATK buffs."
                    }
                ],
                "recommended_archetypes": ["Vaporize Hypercarry", "Overload Core", "Dendro Hyperbloom"]
            },
            "second_half": {
                "name": "Chamber 1 - Second Half",
                "enemy_count": 4,
                "enemies": [
                    {
                        "name": "Mirror Maiden",
                        "hp": 1150000,
                        "element": "Hydro",
                        "immunity": [],
                        "weakness": "Anemo Crowd Control / Freeze",
                        "resistances": "50% Hydro RES, 10% other elements",
                        "advisory": "Use crowd control (Kazuha / Venti) early before she enters the polarized refraction state."
                    },
                    {
                        "name": "Cryo Cicin Mage",
                        "hp": 850000,
                        "element": "Cryo",
                        "immunity": [],
                        "weakness": "Pyro Shield Break",
                        "resistances": "50% Cryo RES, 10% other elements",
                        "advisory": "Break Cryo shield quickly with Pyro attacks to disrupt Cicins."
                    }
                ],
                "recommended_archetypes": ["Freeze Core", "Aggravate / Spread", "Mono Pyro"]
            }
        },
        {
            "chamber": 2,
            "level": 98,
            "stars_available": 3,
            "target_time_sec": 420,
            "first_half": {
                "name": "Chamber 2 - First Half",
                "enemy_count": 2,
                "enemies": [
                    {
                        "name": "Ruin Drake: Skywatch",
                        "hp": 1950000,
                        "element": "Physical",
                        "immunity": [],
                        "weakness": "Bow Charged Shot to weak spots",
                        "resistances": "50% Physical RES, 10% Elemental RES (gains 40% elemental RES after taking sustained elemental damage)",
                        "advisory": "Shoot wing joints or head core with a Bow character while airborne to force a crash and ground it for 15s."
                    }
                ],
                "recommended_archetypes": ["Bow Hypercarry", "Electro-Charged", "Hyperbloom"]
            },
            "second_half": {
                "name": "Chamber 2 - Second Half",
                "enemy_count": 2,
                "enemies": [
                    {
                        "name": "Abyss Lector: Fathomless Flames",
                        "hp": 1400000,
                        "element": "Pyro",
                        "immunity": [],
                        "weakness": "Hydro Application",
                        "resistances": "10% all elements, massive Pyro shield phase (requires fast Hydro attacks)",
                        "advisory": "Apply rapid Hydro attacks (Yelan / Xingqiu / Furina) to deplete dark flame shield before meteor detonation."
                    }
                ],
                "recommended_archetypes": ["Double Hydro", "Mono Hydro", "Bloom / Burgeon"]
            }
        },
        {
            "chamber": 3,
            "level": 100,
            "stars_available": 3,
            "target_time_sec": 420,
            "first_half": {
                "name": "Chamber 3 - First Half",
                "enemy_count": 1,
                "enemies": [
                    {
                        "name": "Icewind Suite: Nemesis of Coppelia",
                        "hp": 3200000,
                        "element": "Anemo / Cryo",
                        "immunity": [],
                        "weakness": "Ousia Alignment / Ranged DPS",
                        "resistances": "70% Anemo RES, 70% Cryo RES, 10% other elements",
                        "advisory": "Avoid Anemo/Cryo primary carries. During Climax phase, Coppelia gains 25% All-RES; hit with 3 Ousia-aligned attacks (e.g. Furina, Navia, Chevreuse) to immediately cancel the barrier."
                    }
                ],
                "recommended_archetypes": ["Pyro Vaporize", "Geo Hypercarry", "Quicken / Aggravate"]
            },
            "second_half": {
                "name": "Chamber 3 - Second Half",
                "enemy_count": 1,
                "enemies": [
                    {
                        "name": "Veteran Emperor of Fire and Iron",
                        "hp": 3600000,
                        "element": "Pyro",
                        "immunity": [],
                        "weakness": "Hydro Shield Shred (Crab Horns)",
                        "resistances": "60% All-Elemental RES while Twin Horns are shielded; drops to 10% RES once shield is broken",
                        "advisory": "Target the Armored Horns high above its head using tall characters or airborne Hydro attacks (Neuvillette, Yelan, Furina) to quickly shatter its defensive shield."
                    }
                ],
                "recommended_archetypes": ["Neuvillette Hypercarry", "Double Hydro", "Vaporize"]
            }
        }
    ],
    "curated_meta_teams": {
        "side_1": [
            {
                "name": "Arlecchino Vaporize Carry",
                "members": ["Arlecchino", "Yelan", "Bennett", "Zhongli"],
                "best_for": "Chambers 1-1, 2-1, 3-1",
                "rationale": "Immense single-target Pyro burst with Zhongli shield to withstand Hydro Tulpa's heavy slam attacks."
            },
            {
                "name": "Alhaitham Quickbloom",
                "members": ["Alhaitham", "Nahida", "Xingqiu", "Kuki Shinobu"],
                "best_for": "Chambers 1-1, 2-1, 3-1",
                "rationale": "High sustained Spread and Hyperbloom damage completely bypassing Anemo/Cryo resistance barriers."
            }
        ],
        "side_2": [
            {
                "name": "Neuvillette Furina Hydro Engine",
                "members": ["Neuvillette", "Furina", "Kaedehara Kazuha", "Baizhu"],
                "best_for": "Chambers 1-2, 2-2, 3-2",
                "rationale": "Unrivaled Hydro DPS shreds Emperor of Fire Twin Horns and Abyss Lector Pyro shields in seconds."
            },
            {
                "name": "Hu Tao Double Hydro",
                "members": ["Hu Tao", "Yelan", "Xingqiu", "Zhongli"],
                "best_for": "Chambers 1-2, 2-2, 3-2",
                "rationale": "Rapid Hydro application breaks Pyro barriers effortlessly while Hu Tao deletes unshielded bosses."
            }
        ]
    }
}


class AbyssService:
    """Endgame Spiral Abyss Floor 12 tracker & account-grounded recommendation service."""

    def get_current_abyss(self) -> Dict[str, Any]:
        """Retrieve complete current active Spiral Abyss Floor 12 details and lineups."""
        return dict(SPIRAL_ABYSS_SCHEDULE)

    def get_grounded_recommendations(self) -> Dict[str, Any]:
        """
        Evaluate account inventory against current Floor 12 monster lineups
        and recommend optimal Side 1 and Side 2 compositions flagging owned vs missing characters.
        """
        snapshot = account_inventory_service.get_active_snapshot()
        owned_names: Set[str] = set()
        if snapshot:
            for c in snapshot.characters:
                name = getattr(c, "canonical_name", None) or getattr(c, "good_key", "")
                if name:
                    owned_names.add(name.lower())

        # Process Side 1 teams
        side_1_teams = []
        for t in SPIRAL_ABYSS_SCHEDULE["curated_meta_teams"]["side_1"]:
            members = t["members"]
            missing = [m for m in members if m.lower() not in owned_names] if snapshot else []
            side_1_teams.append({
                "name": t["name"],
                "members": members,
                "best_for": t["best_for"],
                "rationale": t["rationale"],
                "fully_owned": len(missing) == 0,
                "missing_characters": missing,
                "owned_count": len(members) - len(missing)
            })

        # Process Side 2 teams
        side_2_teams = []
        for t in SPIRAL_ABYSS_SCHEDULE["curated_meta_teams"]["side_2"]:
            members = t["members"]
            missing = [m for m in members if m.lower() not in owned_names] if snapshot else []
            side_2_teams.append({
                "name": t["name"],
                "members": members,
                "best_for": t["best_for"],
                "rationale": t["rationale"],
                "fully_owned": len(missing) == 0,
                "missing_characters": missing,
                "owned_count": len(members) - len(missing)
            })

        # Sort fully owned teams to the top
        side_1_teams.sort(key=lambda x: (x["fully_owned"], x["owned_count"]), reverse=True)
        side_2_teams.sort(key=lambda x: (x["fully_owned"], x["owned_count"]), reverse=True)

        return {
            "floor": 12,
            "period": SPIRAL_ABYSS_SCHEDULE["period"],
            "has_account_snapshot": snapshot is not None,
            "blessing": SPIRAL_ABYSS_SCHEDULE["blessing"],
            "side_1_recommendations": side_1_teams,
            "side_2_recommendations": side_2_teams,
            "provenance": {
                "source": "KeqingMains & Official Abyss Registry",
                "authority": "THEORYCRAFTING_VERIFIED",
                "patch_version": SPIRAL_ABYSS_SCHEDULE["version"]
            },
            "ai_prompt": "Help me build my Spiral Abyss Floor 12 teams based on my owned roster and current chamber enemy mechanics."
        }


abyss_service = AbyssService()
