"""
Team Building & Composition Engine (Phase 14).
Provides deterministic elemental resonance calculation, role synergy scoring,
rotation generation, and account-grounded team recommendations.
"""

from typing import Dict, Any, List, Optional, Set
from collections import Counter

from backend.services.game_data_service import game_data_service
from backend.services.account_inventory_service import account_inventory_service


ELEMENTAL_RESONANCES = {
    "Pyro": {
        "name": "Fervent Flames",
        "effect": "Increases ATK by 25%. Affected by Cryo for 40% less time.",
        "atk_pct": 25.0
    },
    "Hydro": {
        "name": "Soothing Water",
        "effect": "Increases Max HP by 25%. Affected by Pyro for 40% less time.",
        "hp_pct": 25.0
    },
    "Anemo": {
        "name": "Impetuous Winds",
        "effect": "Decreases Stamina Consumption by 15%. Increases Movement SPD by 10%. Shortens Skill CD by 5%.",
        "cd_reduction_pct": 5.0
    },
    "Electro": {
        "name": "High Voltage",
        "effect": "Superconduct, Overloaded, Electro-Charged, Quicken, Aggravate, or Hyperbloom have a 100% chance to generate an Electro Particle (CD 5s).",
        "particle_generation": True
    },
    "Dendro": {
        "name": "Sprawling Greenery",
        "effect": "Increases Elemental Mastery by 50. After triggering reactions, further boosts EM by up to 50 (total 100).",
        "em_flat": 50
    },
    "Cryo": {
        "name": "Shattering Ice",
        "effect": "Increases CRIT Rate against enemies that are Frozen or affected by Cryo by 15%.",
        "crit_rate_pct": 15.0
    },
    "Geo": {
        "name": "Enduring Rock",
        "effect": "Increases Shield Strength by 15%. Shielded characters deal 15% increased DMG and shred enemy Geo RES by 20%.",
        "shield_strength_pct": 15.0,
        "dmg_pct": 15.0
    },
    "Unique": {
        "name": "Protective Canopy",
        "effect": "All Elemental RES +15%, Physical RES +15%.",
        "res_pct": 15.0
    }
}

# Archetype role classification database for prominent characters
CHARACTER_ROLES = {
    # Main DPS / On-field carry
    "arlecchino": "Main DPS", "hu tao": "Main DPS", "neuvillette": "Main DPS",
    "raiden shogun": "Main DPS", "kamisato ayaka": "Main DPS", "alhaitham": "Main DPS",
    "xiao": "Main DPS", "ganyu": "Main DPS", "yoimiya": "Main DPS", "kinich": "Main DPS",
    "mualani": "Main DPS", "navia": "Main DPS", "clorinde": "Main DPS", "lyney": "Main DPS",
    "wriothesley": "Main DPS", "wanderer": "Main DPS", "cyno": "Main DPS", "tartaglia": "Main DPS",
    "arataki itto": "Main DPS", "tighnari": "Main DPS", "eula": "Main DPS", "diluc": "Main DPS",

    # Sub DPS / Off-field damage enabler
    "furina": "Sub-DPS", "xiangling": "Sub-DPS", "xingqiu": "Sub-DPS", "yelan": "Sub-DPS",
    "nahida": "Sub-DPS", "fischl": "Sub-DPS", "yae miko": "Sub-DPS", "rosaria": "Sub-DPS",
    "beidou": "Sub-DPS", "albedo": "Sub-DPS", "chiori": "Sub-DPS", "emilie": "Sub-DPS",

    # Buffer / Utility / Swirl
    "kaedehara kazuha": "Buffer", "bennett": "Buffer", "xianyun": "Buffer",
    "shenhe": "Buffer", "faruzan": "Buffer", "gorou": "Buffer", "kujou sara": "Buffer",
    "sucrose": "Buffer", "venti": "Buffer", "yun jin": "Buffer", "mona": "Buffer",

    # Sustain / Healer / Shielder
    "zhongli": "Sustain", "sangonomiya kokomi": "Sustain", "baizhu": "Sustain",
    "kuki shinobu": "Sustain", "diona": "Sustain", "layla": "Sustain", "kirara": "Sustain",
    "jean": "Sustain", "chevreuse": "Sustain", "charlotte": "Sustain", "yaoyao": "Sustain",
    "barbara": "Sustain", "qiqi": "Sustain", "noelle": "Sustain", "thoma": "Sustain",
    "sigewinne": "Sustain"
}


class TeamService:
    """Evaluates team composition synergy, elemental resonance, and balance."""

    def evaluate_team(self, character_names: List[str]) -> Dict[str, Any]:
        """
        Evaluate a team of 1-4 characters:
        - Resolves entities from canonical database.
        - Calculates active elemental resonances.
        - Analyzes role balance (Main DPS, Sub-DPS, Buffer, Sustain).
        - Unlocks elemental reactions.
        - Computes deterministic synergy score (0 to 100).
        - Generates combat rotation sequence.
        """
        if not character_names:
            return {"error": "Team character list cannot be empty."}

        # Resolve characters
        resolved_chars = []
        invalid_names = []
        for name in character_names:
            char = game_data_service.get_character(name)
            if char:
                resolved_chars.append(char)
            else:
                invalid_names.append(name)

        if invalid_names:
            return {
                "error": f"Unknown character(s): {', '.join(invalid_names)}",
                "valid": False
            }

        if len(resolved_chars) > 4:
            return {"error": "Team cannot exceed 4 characters.", "valid": False}

        # 1. Elemental Resonance
        resonances = self._calculate_resonances(resolved_chars)

        # 2. Roles & Balance Breakdown
        roles_breakdown = []
        role_counts = Counter()
        for c in resolved_chars:
            r = CHARACTER_ROLES.get(c.name.lower(), "Sub-DPS / Flex")
            roles_breakdown.append({
                "name": c.name,
                "element": c.element,
                "weapon_type": c.weapon_type,
                "rarity": c.rarity,
                "role": r
            })
            role_counts[r] += 1

        # 3. Elemental Reactions Unlocked
        elements = set(c.element for c in resolved_chars)
        reactions = self._calculate_reactions(elements)

        # 4. Synergy Scoring (0-100)
        score_breakdown = {}
        synergy_score = 0

        # Resonances (+20 pts max)
        if resonances:
            res_pts = min(20, len(resonances) * 15)
            synergy_score += res_pts
            score_breakdown["Resonance Bonus"] = f"+{res_pts} pts ({', '.join(r['name'] for r in resonances)})"

        # Role Balance (+30 pts max)
        has_main = role_counts["Main DPS"] >= 1
        has_sub = role_counts["Sub-DPS"] >= 1
        has_buffer = role_counts["Buffer"] >= 1
        has_sustain = role_counts["Sustain"] >= 1

        balance_pts = 0
        if has_main: balance_pts += 10
        if has_sub or has_buffer: balance_pts += 10
        if has_sustain: balance_pts += 10
        synergy_score += balance_pts
        score_breakdown["Role Distribution"] = f"+{balance_pts}/30 pts"

        # Reactions (+30 pts max)
        reaction_pts = min(30, len(reactions) * 10)
        synergy_score += reaction_pts
        score_breakdown["Elemental Reactions"] = f"+{reaction_pts}/30 pts ({len(reactions)} reaction types)"

        # Penalty for 0 sustain in 4-man team (-10 pts)
        warnings = []
        if len(resolved_chars) == 4 and not has_sustain:
            synergy_score = max(0, synergy_score - 10)
            warnings.append("Glass Cannon Warning: Team has no dedicated shielder or healer for high-tier Abyss chambers.")

        if role_counts["Main DPS"] > 2:
            synergy_score = max(0, synergy_score - 15)
            warnings.append("On-field Conflict: Multiple Main DPS characters compete for field time and skill uptime.")

        # Full 4-man completion bonus (+20 pts)
        if len(resolved_chars) == 4:
            synergy_score += 20
            score_breakdown["Full Roster Bonus"] = "+20 pts"

        synergy_score = min(100, max(0, synergy_score))

        # 5. Suggested Rotation
        rotation_flow = self._generate_team_rotation(roles_breakdown)

        return {
            "valid": True,
            "team_size": len(resolved_chars),
            "characters": roles_breakdown,
            "synergy_score": synergy_score,
            "verdict": self._score_verdict(synergy_score),
            "score_breakdown": score_breakdown,
            "active_resonances": resonances,
            "elemental_reactions": reactions,
            "rotation_flow": rotation_flow,
            "warnings": warnings,
            "ai_prompt": f"Analyze my team composition: {', '.join(c.name for c in resolved_chars)}. How can I optimize artifacts, weapons, and execution rotations?"
        }

    def recommend_teams(
        self,
        focal_character_name: str,
        owned_only: bool = False
    ) -> Dict[str, Any]:
        """
        Recommend top synergistic team compositions centered around a focal character.
        If owned_only=True, prioritizes characters present in the user's active account snapshot.
        """
        focal_char = game_data_service.get_character(focal_character_name)
        if not focal_char:
            return {"error": f"Character '{focal_character_name}' not found."}

        # Check account ownership
        owned_names: Set[str] = set()
        snapshot = account_inventory_service.get_active_snapshot()
        if snapshot:
            for c in snapshot.characters:
                c_name = getattr(c, "canonical_name", None) or getattr(c, "good_key", "")
                if c_name:
                    owned_names.add(c_name.lower())

        # Curated Archetypes
        archetypes = self._get_curated_archetypes_for_character(focal_char)

        recommended_teams = []
        for arch in archetypes:
            teammates = arch["members"]
            # Check ownership of teammates
            missing = [m for m in teammates if m.lower() not in owned_names and m.lower() != focal_char.name.lower()]
            is_fully_owned = len(missing) == 0 if snapshot else True

            if owned_only and not is_fully_owned and snapshot:
                continue

            eval_res = self.evaluate_team([focal_char.name] + [m for m in teammates if m.lower() != focal_char.name.lower()])

            recommended_teams.append({
                "team_name": arch["name"],
                "archetype": arch["archetype"],
                "members": teammates,
                "summary": arch["summary"],
                "synergy_score": eval_res.get("synergy_score", 85),
                "rotation_steps": arch.get("rotation", []),
                "fully_owned_on_account": is_fully_owned,
                "missing_from_account": missing if snapshot else []
            })

        return {
            "focal_character": focal_char.name,
            "total_recommendations": len(recommended_teams),
            "teams": recommended_teams,
            "has_account_snapshot": snapshot is not None,
            "ai_actions": [
                {"label": "✨ Review Best Team", "prompt": f"Which of the recommended teams for {focal_char.name} will give me the highest DPS?"},
                {"label": "✨ Find F2P Substitutes", "prompt": f"What are good 4-star F2P replacements for {focal_char.name}'s premium team slots?"}
            ]
        }

    # =========================================================================
    # INTERNAL CALCULATIONS
    # =========================================================================

    def _calculate_resonances(self, chars: List[Any]) -> List[Dict[str, Any]]:
        """Calculate elemental resonances from character roster."""
        if len(chars) < 2:
            return []

        counts = Counter(c.element for c in chars)
        resonances = []

        for elem, count in counts.items():
            if count >= 2 and elem in ELEMENTAL_RESONANCES:
                resonances.append(ELEMENTAL_RESONANCES[elem])

        # 4 unique elements
        if len(counts) == 4 and len(chars) == 4 and not resonances:
            resonances.append(ELEMENTAL_RESONANCES["Unique"])

        return resonances

    def _calculate_reactions(self, elements: Set[str]) -> List[Dict[str, str]]:
        """Determine elemental reactions unlocked by party elements."""
        reactions = []
        if "Pyro" in elements and "Hydro" in elements:
            reactions.append({"name": "Vaporize", "type": "Amplifying", "effect": "1.5x - 2.0x DMG multiplier."})
        if "Pyro" in elements and "Cryo" in elements:
            reactions.append({"name": "Melt", "type": "Amplifying", "effect": "1.5x - 2.0x DMG multiplier."})
        if "Electro" in elements and "Hydro" in elements:
            reactions.append({"name": "Electro-Charged", "type": "Transformative", "effect": "Continuous chain lightning damage."})
        if "Cryo" in elements and "Hydro" in elements:
            reactions.append({"name": "Freeze", "type": "Crowd Control", "effect": "Freezes targets solid."})
        if "Dendro" in elements and "Hydro" in elements:
            reactions.append({"name": "Bloom", "type": "Transformative", "effect": "Spawns Dendro Cores."})
        if "Dendro" in elements and "Electro" in elements:
            reactions.append({"name": "Quicken (Aggravate / Spread)", "type": "Additive", "effect": "Flat additive base damage boost."})
        if "Dendro" in elements and "Hydro" in elements and "Electro" in elements:
            reactions.append({"name": "Hyperbloom", "type": "Transformative", "effect": "Fires high-damage homing Sprawling Shots."})
        if "Pyro" in elements and "Electro" in elements:
            reactions.append({"name": "Overloaded", "type": "Transformative", "effect": "AoE Pyro explosion & high poise break."})
        if "Anemo" in elements and len(elements - {"Anemo", "Geo", "Dendro"}) > 0:
            reactions.append({"name": "Swirl", "type": "Transformative / Shred", "effect": "Spreads elements & triggers 4pc VV 40% RES shred."})
        if "Geo" in elements and len(elements - {"Geo", "Anemo", "Dendro"}) > 0:
            reactions.append({"name": "Crystallize", "type": "Defensive", "effect": "Drops elemental shield shards."})

        return reactions

    def _generate_team_rotation(self, roles: List[Dict[str, Any]]) -> List[str]:
        """Order execution steps: Shielder/Sustain -> Buffer -> Sub-DPS -> Main DPS."""
        steps = []
        # Sort characters by execution priority: Sustain (shields/healing) first, then Buffer, then Sub-DPS, then Main DPS
        priority_map = {"Sustain": 1, "Buffer": 2, "Sub-DPS": 3, "Main DPS": 4}
        sorted_roles = sorted(roles, key=lambda r: priority_map.get(r["role"], 3))

        for idx, char in enumerate(sorted_roles, 1):
            role = char["role"]
            name = char["name"]
            if role == "Sustain":
                steps.append(f"{idx}. {name}: Cast Skill / Shield to establish defensive uptime and poise resistance.")
            elif role == "Buffer":
                steps.append(f"{idx}. {name}: Unleash Burst & Skill for party-wide stat buffs and resistance shred.")
            elif role == "Sub-DPS":
                steps.append(f"{idx}. {name}: Deploy off-field Burst / Skill to enable elemental reactions.")
            else:
                steps.append(f"{idx}. {name}: Take the field, execute skill rotation, and deal primary combat damage.")

        return steps

    def _score_verdict(self, score: int) -> str:
        if score >= 90: return "S-Tier Synergy: Outstanding role balance, resonance, and reaction coverage."
        if score >= 75: return "A-Tier Synergy: Strong team configuration with reliable combat uptime."
        if score >= 60: return "B-Tier Synergy: Functional composition; could benefit from dedicated sustain or buffer."
        return "C-Tier Synergy: Suboptimal role overlap or conflicting on-field requirements."

    def _get_curated_archetypes_for_character(self, char: Any) -> List[Dict[str, Any]]:
        """Return curated team archetypes based on element and kit."""
        name = char.name
        elem = char.element

        if name == "Arlecchino":
            return [
                {
                    "name": "Arlecchino Vaporize",
                    "archetype": "Vaporize",
                    "members": ["Arlecchino", "Yelan", "Bennett", "Zhongli"],
                    "summary": "Classic vaporize hypercarry setup pairing Hydro application with massive Pyro scaling.",
                    "rotation": [
                        "1. Zhongli: Hold Skill for Jade Shield and RES shred.",
                        "2. Bennett: Burst (Inspiration Field) + Skill.",
                        "3. Yelan: Burst (Exquisite Throw) + Skill.",
                        "4. Arlecchino: Skill -> wait for blood debt -> Charged Attack -> Normal Attack strings."
                    ]
                },
                {
                    "name": "Arlecchino Chevreuse Overload",
                    "archetype": "Overload",
                    "members": ["Arlecchino", "Chevreuse", "Fischl", "Bennett"],
                    "summary": "Dual Pyro/Electro overload team utilizing Chevreuse's 40% Pyro/Electro shred and 40% ATK buff.",
                    "rotation": [
                        "1. Fischl: Skill (Oz) to trigger initial Electro application.",
                        "2. Chevreuse: Hold Skill (Overcharged Ball) for RES shred and party ATK buff.",
                        "3. Bennett: Burst for massive flat ATK addition.",
                        "4. Arlecchino: Collect blood debt and execute devastating Normal Attacks."
                    ]
                }
            ]

        if name == "Furina":
            return [
                {
                    "name": "Furina Neuvillette Hydro Hypercarry",
                    "archetype": "Mono Hydro / Vaporize",
                    "members": ["Neuvillette", "Furina", "Kaedehara Kazuha", "Baizhu"],
                    "summary": "Unrivaled team damage pairing Neuvillette's HP fluctuations with Furina's maximum Fanfare stacks.",
                    "rotation": [
                        "1. Furina: Skill (Salon Solitaire) + Burst (Let the People Rejoice).",
                        "2. Baizhu: Skill + Burst for party healing and Fanfare generation.",
                        "3. Kazuha: Skill + Burst for 40% Hydro shred and DMG bonus.",
                        "4. Neuvillette: Unleash continuous Equitable Judgment Charged Attacks."
                    ]
                }
            ]

        # Generic element-based fallback archetypes
        if elem == "Hydro":
            return [
                {
                    "name": f"{name} Taser Reaction",
                    "archetype": "Electro-Charged",
                    "members": [name, "Fischl", "Beidou", "Kaedehara Kazuha"],
                    "summary": "Continuous chain-lightning electro-charged damage with high AoE crowd control.",
                    "rotation": ["1. Apply Hydro with Skill", "2. Swirl with Kazuha", "3. Cast Fischl Oz", "4. Drive with Normal Attacks"]
                }
            ]

        if elem == "Cryo":
            return [
                {
                    "name": f"{name} Freeze Core",
                    "archetype": "Freeze",
                    "members": [name, "Furina", "Kaedehara Kazuha", "Charlotte"],
                    "summary": "100% frozen uptime with blizzard strayer 40% CRIT Rate bonus.",
                    "rotation": ["1. Apply Cryo", "2. Swirl with Kazuha", "3. Freeze with Furina", "4. Execute Cryo Burst"]
                }
            ]

        # Default versatile setup
        return [
            {
                "name": f"{name} National Core",
                "archetype": "Vaporize / Swirl",
                "members": [name, "Xiangling", "Xingqiu", "Bennett"],
                "summary": "Universal national engine providing unmatched off-field Vaporize damage.",
                "rotation": ["1. Bennett Burst", "2. Xingqiu Burst", "3. Xiangling Pyronado", f"4. {name} on-field attacks"]
            }
        ]

    def get_resonances(self) -> Dict[str, Any]:
        """Return canonical elemental resonance descriptions and stat boosts."""
        return ELEMENTAL_RESONANCES


team_service = TeamService()

