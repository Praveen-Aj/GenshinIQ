import json
from pathlib import Path
from backend.services.character_knowledge_service import character_knowledge_service

base_gaps = {
  "schema_version": "1.0",
  "updated_at": "2026-09-12T08:00:00.000000+00:00",
  "total_gaps_tracked": 3,
  "gaps": [
    {
      "gap_id": "gap_natlan_nightsoul_burst_gauge_consumption",
      "topic": "Game Mechanics",
      "entity": "Natlan Nightsoul & Phlogiston Systems",
      "version": "5.0+",
      "question": "What are the exact Nightsoul Transmission point decay rates and Phlogiston consumption curves while traversing steep cliff faces vs lava terrain in Natlan?",
      "status": "OPEN_INVESTIGATING",
      "recommended_source": "src_kqm_tcl",
      "notes": "Ongoing measurement in KQM TCL; exact terrain angle multipliers have not yet been fully parameterized into structured data."
    },
    {
      "gap_id": "gap_plunge_collision_damage_scaling",
      "topic": "Game Mechanics",
      "entity": "Plunge Attack Physics & Xianyun Synergy",
      "version": "4.4+",
      "question": "What is the exact low-plunge vs high-plunge collision hitbox radius and damage falloff percentage for claymore characters during Xianyun high jumps?",
      "status": "OPEN_INVESTIGATING",
      "recommended_source": "src_kqm_tcl",
      "notes": "Low vs high plunge threshold is determined by vertical fall duration (approx 0.3s cutoff); hitlag interaction against flying enemies requires further verified empirical data."
    },
    {
      "gap_id": "gap_spiral_abyss_12_poise_decay_rates",
      "topic": "Combat Theorycrafting",
      "entity": "Elite Consecrated & Local Legend Enemies",
      "version": "5.0+",
      "question": "What are the exact Poise Health recovery rates and stagger immunity cooldown windows for Natlan Local Legends (e.g., Cautious Balachko, Polychrome Tri-Stars)?",
      "status": "AWAITING_SOURCE",
      "recommended_source": "src_kqm_tcl",
      "notes": "Local legends possess modified stagger thresholds that do not conform to standard humanoid 100 poise bar recovery; awaiting standardized poise data catalog."
    }
  ]
}

with open("data/canonical/knowledge_gaps.json", "w", encoding="utf-8") as f:
    json.dump(base_gaps, f, indent=2)

pkgs = character_knowledge_service.list_all_packages()
character_knowledge_service.save_packages_registry()
print(f"Compiled {len(pkgs)} character packages.")

with open("data/canonical/knowledge_gaps.json", "r", encoding="utf-8") as f:
    gaps_data = json.load(f)

print(f"Total gaps tracked now: {gaps_data['total_gaps_tracked']}")
for g in gaps_data["gaps"]:
    print(f"  - {g['gap_id']} : {g.get('entity', '')}")
