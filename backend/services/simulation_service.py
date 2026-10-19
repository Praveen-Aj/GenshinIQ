"""
Combat Simulation Engine & gcsim Integration (Phase 16).
Provides gcsim configuration generation, rotation sequence parsing,
and deterministic mathematical rotation modeling with DPS graphs
and party damage breakdowns.
"""

from typing import Dict, Any, List, Optional
import math
import logging

from backend.services.game_data_service import game_data_service
from backend.services.team_service import team_service

logger = logging.getLogger(__name__)

# Base motion values and scaling factors for benchmark simulation
CHARACTER_ROTATION_PROFILES = {
    "arlecchino": {
        "role": "Main DPS",
        "element": "Pyro",
        "mv_per_sec": 480.0,  # Motion value % per second during infusion
        "field_time_sec": 12.0,
        "energy_cost": 60,
        "reaction_rate": 0.5  # 50% of attacks vape in standard ICD
    },
    "hu tao": {
        "role": "Main DPS",
        "element": "Pyro",
        "mv_per_sec": 520.0,
        "field_time_sec": 9.0,
        "energy_cost": 60,
        "reaction_rate": 0.85 # High vape rate on charged attacks
    },
    "neuvillette": {
        "role": "Main DPS",
        "element": "Hydro",
        "mv_per_sec": 550.0,
        "field_time_sec": 12.0,
        "energy_cost": 70,
        "reaction_rate": 0.0  # Raw Hydro scaling
    },
    "furina": {
        "role": "Sub-DPS / Buffer",
        "element": "Hydro",
        "mv_per_sec": 180.0,  # Off-field Salon Solitaire
        "buff_dmg_pct": 75.0, # Max Fanfare DMG bonus
        "field_time_sec": 2.5,
        "energy_cost": 60,
        "reaction_rate": 0.3
    },
    "yelan": {
        "role": "Sub-DPS",
        "element": "Hydro",
        "mv_per_sec": 260.0,  # Exquisite Throw
        "buff_dmg_pct": 25.0, # Average ramping DMG% bonus
        "field_time_sec": 2.5,
        "energy_cost": 70,
        "reaction_rate": 0.0
    },
    "xingqiu": {
        "role": "Sub-DPS",
        "element": "Hydro",
        "mv_per_sec": 220.0,  # Raincutter
        "field_time_sec": 2.5,
        "energy_cost": 80,
        "reaction_rate": 0.0
    },
    "xiangling": {
        "role": "Sub-DPS",
        "element": "Pyro",
        "mv_per_sec": 310.0,  # Pyronado no ICD
        "field_time_sec": 2.0,
        "energy_cost": 80,
        "reaction_rate": 0.8
    },
    "kaedehara kazuha": {
        "role": "Buffer",
        "element": "Anemo",
        "mv_per_sec": 120.0,
        "buff_dmg_pct": 36.0, # 900 EM * 0.04%
        "res_shred_pct": 40.0, # 4pc VV
        "field_time_sec": 2.5,
        "energy_cost": 60,
        "reaction_rate": 0.0
    },
    "bennett": {
        "role": "Buffer",
        "element": "Pyro",
        "mv_per_sec": 80.0,
        "flat_atk_buff": 1100.0, # Base ATK * 1.2
        "field_time_sec": 2.0,
        "energy_cost": 60,
        "reaction_rate": 0.0
    },
    "zhongli": {
        "role": "Sustain",
        "element": "Geo",
        "mv_per_sec": 40.0,
        "res_shred_pct": 20.0, # Jade Shield
        "field_time_sec": 2.0,
        "energy_cost": 40,
        "reaction_rate": 0.0
    }
}


class SimulationService:
    """Combat simulation service integrating gcsim syntax and deterministic math."""

    def generate_gcsim_config(
        self,
        character_names: List[str],
        duration_sec: int = 90,
        iterations: int = 1000
    ) -> Dict[str, Any]:
        """
        Generate a fully formed, valid gcsim configuration script (.txt)
        for the given 4-man team composition.
        """
        if not character_names:
            return {"error": "Character list cannot be empty."}

        # Resolve characters
        resolved = []
        for name in character_names:
            char = game_data_service.get_character(name)
            if not char:
                return {"error": f"Character '{name}' not found in canonical database."}
            resolved.append(char)

        lines = [
            f"# ========================================================",
            f"# GenshinIQ Auto-Generated gcsim Configuration",
            f"# Team: {', '.join(c.name for c in resolved)}",
            f"# Target: Single Target Level 100 Dummy (10% all RES)",
            f"# ========================================================",
            "",
            f"options debug=true iteration={iterations} duration={duration_sec} workers=4;",
            "",
            "# Target definition: Lv 100 dummy with standard 10% all-element resistance",
            "target lvl=100 pos=0,2.5 radius=1.0 hp=99999999 electro=0.1 pyro=0.1 hydro=0.1 cryo=0.1 anemo=0.1 geo=0.1 dendro=0.1 phys=0.1;",
            ""
        ]

        # Generate character definitions
        for c in resolved:
            clean_name = c.name.lower().replace(" ", "").replace("-", "")
            lines.extend([
                f"# Character: {c.name}",
                f"{clean_name} char lvl=90/90 cons=0 talent=9,9,9;",
                f"{clean_name} add weapon=\"favoniussword\" lvl=90/90 refine=5;",
                f"{clean_name} add set=\"gladiator\" count=2;",
                f"{clean_name} add set=\"noblesse\" count=2;",
                f"{clean_name} add stats hp=4780 atk=311 cr=0.60 cd=1.20 er=1.30;",
                ""
            ])

        # Active character and rotation sequence
        lines.extend([
            f"active {resolved[0].name.lower().replace(' ', '')};",
            "",
            "# Action execution loop",
            "while 1 {"
        ])

        # Add rotation steps
        for c in resolved:
            c_key = c.name.lower().replace(" ", "")
            lines.append(f"    {c_key} skill, burst;")

        lines.extend([
            "    wait 60;",
            "}",
            ""
        ])

        config_text = "\n".join(lines)
        return {
            "valid": True,
            "team": [c.name for c in resolved],
            "duration_sec": duration_sec,
            "iterations": iterations,
            "gcsim_config": config_text
        }

    def run_deterministic_simulation(
        self,
        character_names: List[str],
        duration_sec: int = 20,
        enemy_count: int = 1,
        enemy_res_pct: float = 10.0
    ) -> Dict[str, Any]:
        """
        Execute deterministic mathematical simulation of combat rotation.
        Computes second-by-second damage curves, party DPS, motion value execution,
        and elemental reaction contributions.
        """
        if not character_names:
            return {"error": "Character list cannot be empty."}

        resolved = []
        for name in character_names:
            char = game_data_service.get_character(name)
            if not char:
                return {"error": f"Character '{name}' not found."}
            resolved.append(char)

        # Team synergy evaluation
        team_eval = team_service.evaluate_team(character_names)

        # Base party buffs
        total_buff_dmg = 0.0
        total_res_shred = 0.0
        total_flat_atk = 0.0

        for c in resolved:
            prof = CHARACTER_ROTATION_PROFILES.get(c.name.lower(), {})
            total_buff_dmg += prof.get("buff_dmg_pct", 0.0)
            total_res_shred += prof.get("res_shred_pct", 0.0)
            total_flat_atk += prof.get("flat_atk_buff", 0.0)

        # Effective enemy resistance multiplier
        effective_res = (enemy_res_pct - total_res_shred) / 100.0
        if effective_res < 0:
            res_multiplier = 1.0 - (effective_res / 2.0)
        elif effective_res <= 0.75:
            res_multiplier = 1.0 - effective_res
        else:
            res_multiplier = 1.0 / (4.0 * effective_res + 1.0)

        # Defense multiplier for Lv 90 char vs Lv 100 enemy
        # (90 + 100) / ((90 + 100) + (100 + 100)) = 190 / 390 = 0.487
        def_multiplier = 0.487

        # Per-character contribution calculations
        character_dps = {}
        elemental_dmg = {
            "Pyro": 0.0, "Hydro": 0.0, "Anemo": 0.0,
            "Electro": 0.0, "Dendro": 0.0, "Cryo": 0.0, "Geo": 0.0, "Physical": 0.0
        }

        total_damage = 0.0
        second_by_second_dmg = []

        # Standard rotation length
        rotation_window = min(duration_sec, 20)

        for sec in range(1, duration_sec + 1):
            sec_damage = 0.0
            for c in resolved:
                c_name = c.name
                elem = c.element
                prof = CHARACTER_ROTATION_PROFILES.get(c_name.lower(), {
                    "role": "Sub-DPS",
                    "element": elem,
                    "mv_per_sec": 150.0,
                    "field_time_sec": 3.0,
                    "reaction_rate": 0.2
                })

                base_mv = prof.get("mv_per_sec", 150.0)
                # Approximate base scaling (ATK/HP/DEF composite) ~ 2000 base
                base_stat = 2200.0 + (total_flat_atk * 0.5)
                # Crit multiplier (assuming 70% CR, 140% CD) -> 1 + (0.7 * 1.4) = 1.98
                crit_multiplier = 1.98
                # DMG bonus multiplier
                dmg_bonus_mult = 1.0 + ((46.6 + total_buff_dmg) / 100.0)

                # Reaction multiplier
                reaction_mult = 1.0
                if prof.get("reaction_rate", 0.0) > 0 and elem in ("Pyro", "Hydro", "Cryo"):
                    # 1.5x amp reaction
                    reaction_mult = 1.0 + (prof["reaction_rate"] * 0.5)

                char_sec_dmg = base_stat * (base_mv / 100.0) * crit_multiplier * dmg_bonus_mult * reaction_mult * def_multiplier * res_multiplier
                # Scale by enemy count
                char_sec_dmg *= (1.0 + (enemy_count - 1) * 0.45)

                sec_damage += char_sec_dmg
                character_dps[c_name] = character_dps.get(c_name, 0.0) + char_sec_dmg
                elemental_dmg[elem] = elemental_dmg.get(elem, 0.0) + char_sec_dmg

            total_damage += sec_damage
            second_by_second_dmg.append({
                "second": sec,
                "damage": round(sec_damage, 0),
                "cumulative_damage": round(total_damage, 0)
            })

        overall_dps = round(total_damage / duration_sec, 1)

        # Percentage breakdown per character
        char_breakdown = []
        for c_name, dmg in character_dps.items():
            pct = round((dmg / total_damage) * 100.0, 1) if total_damage > 0 else 0.0
            char_breakdown.append({
                "character": c_name,
                "total_damage": round(dmg, 0),
                "dps": round(dmg / duration_sec, 1),
                "damage_share_pct": pct
            })
        char_breakdown.sort(key=lambda x: x["total_damage"], reverse=True)

        # Percentage breakdown per element
        elem_breakdown = []
        for elem, dmg in elemental_dmg.items():
            if dmg > 0:
                elem_breakdown.append({
                    "element": elem,
                    "total_damage": round(dmg, 0),
                    "share_pct": round((dmg / total_damage) * 100.0, 1) if total_damage > 0 else 0.0
                })
        elem_breakdown.sort(key=lambda x: x["total_damage"], reverse=True)

        return {
            "valid": True,
            "engine": "Deterministic Mathematical Model (Genshin Combat Scaling)",
            "simulation_parameters": {
                "team": [c.name for c in resolved],
                "duration_seconds": duration_sec,
                "enemy_count": enemy_count,
                "enemy_resistance_pct": enemy_res_pct,
                "effective_resistance_pct": round(effective_res * 100.0, 1)
            },
            "summary_metrics": {
                "total_damage": round(total_damage, 0),
                "team_dps": overall_dps,
                "synergy_score": team_eval.get("synergy_score", 80),
                "active_resonances": [r["name"] for r in team_eval.get("active_resonances", [])]
            },
            "character_breakdown": char_breakdown,
            "elemental_breakdown": elem_breakdown,
            "dps_timeline": second_by_second_dmg[:30],  # Sample points for visualization
            "ai_prompt": f"My simulated team ({', '.join(c.name for c in resolved)}) deals {overall_dps:,.0f} DPS. How can I alter weapon choices or rotations to increase total damage?"
        }


simulation_service = SimulationService()
